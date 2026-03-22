#!/usr/bin/env bun
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { Bot } from "grammy";

// --- Configuration ---
const TOKEN = process.env.TELEGRAM_BOT_TOKEN;
if (!TOKEN) {
  console.error("TELEGRAM_BOT_TOKEN is required");
  process.exit(1);
}

const ALLOWED_IDS = new Set(
  (process.env.ALLOWED_USER_IDS || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .map(Number)
);

// --- Grammy bot instance ---
const bot = new Bot(TOKEN);

// --- MCP Server ---
const mcp = new Server(
  { name: "telegram", version: "0.0.1" },
  {
    capabilities: {
      experimental: { "claude/channel": {} },
      tools: {},
    },
    instructions: [
      'Telegram messages arrive as <channel source="telegram" chat_id="..." message_id="..." user="..." ts="...">.',
      "Reply using the reply tool, passing the chat_id from the tag.",
      "Always reply to the user in a helpful, conversational tone.",
      "If the message is a question, answer it. If it's a greeting, greet back.",
    ].join(" "),
  }
);

// --- Reply tool: lets Claude send messages back to Telegram ---

function splitMessage(text: string, limit = 4096): string[] {
  if (text.length <= limit) return [text];
  const chunks: string[] = [];
  let remaining = text;
  while (remaining.length > 0) {
    if (remaining.length <= limit) {
      chunks.push(remaining);
      break;
    }
    // Try to split at last newline within limit
    let splitAt = remaining.lastIndexOf("\n", limit);
    if (splitAt <= 0) splitAt = limit;
    chunks.push(remaining.slice(0, splitAt));
    remaining = remaining.slice(splitAt).replace(/^\n/, "");
  }
  return chunks;
}

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "reply",
      description: "Send a message back to a Telegram chat",
      inputSchema: {
        type: "object" as const,
        properties: {
          chat_id: {
            type: "string",
            description: "The Telegram chat ID to reply in",
          },
          text: { type: "string", description: "The message text to send" },
          reply_to: {
            type: "string",
            description: "Optional message ID to reply to for threading",
          },
        },
        required: ["chat_id", "text"],
      },
    },
  ],
}));

mcp.setRequestHandler(CallToolRequestSchema, async (req) => {
  if (req.params.name === "reply") {
    const { chat_id, text, reply_to } = req.params.arguments as {
      chat_id: string;
      text: string;
      reply_to?: string;
    };

    const chunks = splitMessage(text);
    for (const chunk of chunks) {
      await bot.api.sendMessage(Number(chat_id), chunk, {
        ...(reply_to
          ? { reply_parameters: { message_id: Number(reply_to) } }
          : {}),
      });
    }

    return { content: [{ type: "text", text: "sent" }] };
  }
  throw new Error(`unknown tool: ${req.params.name}`);
});

// --- Connect MCP over stdio ---
await mcp.connect(new StdioServerTransport());
console.error("[telegram-channel] MCP connected");

// --- Telegram message handler ---
bot.on("message:text", async (ctx) => {
  const senderId = ctx.from?.id;

  // Gate: check allowlist
  if (ALLOWED_IDS.size > 0 && (!senderId || !ALLOWED_IDS.has(senderId))) {
    return; // silently drop
  }

  const username =
    ctx.from?.username || ctx.from?.first_name || String(senderId);

  console.error(
    `[telegram-channel] Message from ${username} (${senderId}): ${ctx.message.text.slice(0, 50)}...`
  );

  await mcp.notification({
    method: "notifications/claude/channel",
    params: {
      content: ctx.message.text,
      meta: {
        chat_id: String(ctx.chat.id),
        message_id: String(ctx.message.message_id),
        user: username,
        ts: String(ctx.message.date),
      },
    },
  });
});

// --- Start polling ---
console.error("[telegram-channel] Starting Telegram polling...");
bot.start({
  onStart: (info) => {
    console.error(`[telegram-channel] Bot @${info.username} is running`);
  },
});
