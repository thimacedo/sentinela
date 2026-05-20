import DashboardStats from "@/components/warroom/DashboardStats";

export default function WarRoom() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-tactical-accent mb-6">WAR ROOM</h1>
      <DashboardStats />
      {/* Aqui podem entrar outros componentes do dashboard principal no futuro */}
    </div>
  );
}
