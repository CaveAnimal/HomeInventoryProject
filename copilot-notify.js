function summarizeInput(input) {
  if (input === undefined || input === null) {
    return "(no input)";
  }

  const serialized = typeof input === "string" ? input : JSON.stringify(input);
  return serialized.length > 500 ? `${serialized.slice(0, 500)}...` : serialized;
}

function classifyEvent(toolName, inputSummary) {
  const text = `${toolName} ${inputSummary}`.toLowerCase();

  if (/block|fail|error|exception|timeout|problem|testfailure|get_errors/.test(text)) {
    return { label: "Blocker Signal", emoji: "🚨" };
  }

  if (/plan|phase|complete|completed|manage_todo_list|create_and_run_task/.test(text)) {
    return { label: "Phase Signal", emoji: "✅" };
  }

  return { label: "Progress Signal", emoji: "🔧" };
}

async function sendTelegramMessage(config, message) {
  const endpoint = `https://api.telegram.org/bot${config.telegramBotToken}/sendMessage`;
  const body = {
    chat_id: config.telegramChatId,
    text: message,
    disable_web_page_preview: true
  };

  if (config.telegramThreadId) {
    body.message_thread_id = Number(config.telegramThreadId);
  }

  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Telegram notification failed (${response.status}): ${errorBody}`);
  }
}

async function sendGenericWebhook(config, payload) {
  const response = await fetch(config.webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Webhook notification failed (${response.status}): ${errorBody}`);
  }
}

function resolveConfig(config) {
  const cfg = config || {};

  return {
    telegramBotToken: cfg.telegramBotToken || process.env.TELEGRAM_BOT_TOKEN,
    telegramChatId: cfg.telegramChatId || process.env.TELEGRAM_CHAT_ID,
    telegramThreadId: cfg.telegramThreadId || process.env.TELEGRAM_THREAD_ID,
    webhookUrl: cfg.webhookUrl
  };
}

export default async function copilotNotify(context) {
  const { toolName, input } = context;
  const inputSummary = summarizeInput(input);
  const timestamp = new Date().toISOString();
  const classification = classifyEvent(toolName, inputSummary);

  const payload = {
    event: "copilot_tool_invocation",
    category: classification.label,
    tool: toolName,
    input,
    timestamp
  };

  const cfg = resolveConfig(context.config);

  if (cfg.telegramBotToken && cfg.telegramChatId) {
    const message = [
      `${classification.emoji} ${classification.label}`,
      `Tool: ${toolName}`,
      `Time: ${timestamp}`,
      `Input: ${inputSummary.replace(/`/g, "'")}`
    ].join("\n");

    await sendTelegramMessage(cfg, message);
    return;
  }

  if (cfg.webhookUrl) {
    await sendGenericWebhook(cfg, payload);
    return;
  }

  throw new Error("No notification target configured. Set telegramBotToken + telegramChatId, or webhookUrl.");
}
