import WarRoomOverview from "@/components/warroom/WarRoomOverview";

export default function WarRoom() {
  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-tactical-accent">WAR ROOM</h1>
        <div className="text-[10px] font-mono text-tactical-accent/40">
          SISTEMA SENTINELA // PASA v50.0
        </div>
      </div>
      <WarRoomOverview />
    </div>
  );
}
