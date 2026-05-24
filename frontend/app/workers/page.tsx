'use client';

import QueueTab from "@/components/warroom/QueueTab";

export default function WorkersPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-tactical-accent tracking-tighter uppercase">Status dos Workers</h1>
      <QueueTab />
    </div>
  );
}
