import { useMemo, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import { Alert, Button, Card, Input, Space, Tag, Typography, message } from "antd";
import {
  CloseOutlined,
  CloudUploadOutlined,
  MessageOutlined,
  RobotOutlined,
  SendOutlined,
} from "@ant-design/icons";

import { leaveAuditApi } from "@/api/leaveAuditApi";

const { Text } = Typography;

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

function normalizeOcrText(value: string | string[]): string {
  return Array.isArray(value) ? value.join("\n") : value;
}

export function DifyOcrChatbot() {
  const [open, setOpen] = useState(false);
  const [ocrText, setOcrText] = useState("");
  const [ocrBackend, setOcrBackend] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const canSend = useMemo(() => question.trim().length > 0 && !chatLoading, [chatLoading, question]);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }
    setOcrLoading(true);
    try {
      const response = await leaveAuditApi.runOcr(file, "rapidocr");
      const text = normalizeOcrText(response.text);
      setOcrText(text);
      setOcrBackend(response.ocr_backend);
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-ocr`,
          role: "assistant",
          content: text ? `已完成 OCR：${text.slice(0, 160)}${text.length > 160 ? "..." : ""}` : "OCR 已完成，但未识别到文本。",
        },
      ]);
      message.success("OCR 提取完成");
    } catch (error) {
      message.error(error instanceof Error ? error.message : "OCR 提取失败");
    } finally {
      setOcrLoading(false);
    }
  };

  const sendQuestion = async () => {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      return;
    }
    const userMessage: ChatMessage = {
      id: `${Date.now()}-user`,
      role: "user",
      content: trimmedQuestion,
    };
    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setChatLoading(true);
    try {
      const response = await leaveAuditApi.askDify({
        question: trimmedQuestion,
        ocr_text: ocrText,
        conversation_id: conversationId,
      });
      setConversationId(response.conversation_id ?? null);
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-assistant`,
          role: "assistant",
          content: response.answer,
        },
      ]);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "Dify 问答失败");
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-assistant-error`,
          role: "assistant",
          content: "Dify 暂时没有返回有效答案，请稍后重试。",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="dify-chatbot">
      {open ? (
        <Card
          className="dify-chatbot-panel"
          title={
            <Space>
              <RobotOutlined />
              <span>OCR 问答</span>
            </Space>
          }
          extra={<Button type="text" size="small" icon={<CloseOutlined />} onClick={() => setOpen(false)} />}
        >
          <Space direction="vertical" size={12} className="leave-audit-full-width">
            <Space wrap>
              <Button icon={<CloudUploadOutlined />} loading={ocrLoading} onClick={() => fileInputRef.current?.click()}>
                上传图片 OCR
              </Button>
              {ocrBackend ? <Tag color="blue">{ocrBackend}</Tag> : <Tag>未上传图片</Tag>}
              <input
                ref={fileInputRef}
                className="dify-chatbot-file-input"
                type="file"
                accept="image/*"
                onChange={(event) => void handleFileChange(event)}
              />
            </Space>

            {ocrText ? (
              <div className="dify-chatbot-ocr">
                <Text type="secondary">OCR 文本</Text>
                <pre>{ocrText}</pre>
              </div>
            ) : (
              <Alert type="info" showIcon message="可先上传图片，也可以直接提问。" />
            )}

            <div className="dify-chatbot-messages">
              {messages.length ? (
                messages.map((item) => (
                  <div key={item.id} className={`dify-chatbot-message dify-chatbot-message--${item.role}`}>
                    {item.content}
                  </div>
                ))
              ) : (
                <div className="dify-chatbot-empty">暂无对话</div>
              )}
            </div>

            <Input.TextArea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onPressEnter={(event) => {
                if (!event.shiftKey) {
                  event.preventDefault();
                  void sendQuestion();
                }
              }}
              placeholder="输入问题"
              autoSize={{ minRows: 2, maxRows: 4 }}
            />
            <Button type="primary" icon={<SendOutlined />} block disabled={!canSend} loading={chatLoading} onClick={() => void sendQuestion()}>
              发送
            </Button>
          </Space>
        </Card>
      ) : (
        <Button type="primary" shape="circle" size="large" icon={<MessageOutlined />} onClick={() => setOpen(true)} />
      )}
    </div>
  );
}
