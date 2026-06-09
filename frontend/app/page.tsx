import { Suspense } from "react";
import { AppShell } from "../src/components/AppShell";
import { ChatView } from "../src/components/ChatView";

export const metadata = {
  title: "MindBridge-RAG Study Planner",
  description: "Chat with your own notes. A RAG-powered study planner and exam stress companion.",
};

export default function HomePage() {
  return (
    <AppShell>
      <Suspense fallback={null}>
        <ChatView />
      </Suspense>
    </AppShell>
  );
}
