import { useState } from "react";
import Sidebar from "@/components/chat/Sidebar";
import ChatWindow from "@/components/chat/ChatWindow";

export default function Workspace() {
  const [uploadedDocs, setUploadedDocs] = useState<string[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="h-screen bg-[#0A0F1E] flex overflow-hidden">

      {/* Sidebar */}
      <Sidebar
        docs={uploadedDocs}
        onDocsChange={setUploadedDocs}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />

      {/* Main chat area */}
      <main className={`flex-1 flex flex-col min-w-0 transition-all duration-300`}>
        <ChatWindow
          docs={uploadedDocs}
          onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
          sidebarOpen={sidebarOpen}
        />
      </main>
    </div>
  );
}