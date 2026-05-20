'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import WarRoomOverview from "@/components/warroom/WarRoomOverview";
import ForensicTab from "@/components/warroom/ForensicTab";
import TargetsTab from "@/components/warroom/TargetsTab";
import DossiersTab from "@/components/warroom/DossiersTab";
import AlertsTab from "@/components/warroom/AlertsTab";
import NetworkTab from "@/components/warroom/NetworkTab";
import QueueTab from "@/components/warroom/QueueTab";

export default function DashboardPage() {
  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-tactical-accent">WAR ROOM</h1>
        <div className="text-[10px] font-mono text-tactical-accent/40">
          CENTRAL DE COMANDO // OPERAÇÃO DIAMANTE
        </div>
      </div>
      
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="bg-black/50 border border-tactical-accent/30 p-1 mb-8 overflow-x-auto flex-nowrap justify-start">
          <TabsTrigger value="overview" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6">Geral</TabsTrigger>
          <TabsTrigger value="forensic" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6">Forense</TabsTrigger>
          <TabsTrigger value="targets" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6">Alvos</TabsTrigger>
          <TabsTrigger value="dossiers" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6">Dossiês</TabsTrigger>
          <TabsTrigger value="alerts" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6">Alertas</TabsTrigger>
          <TabsTrigger value="network" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6">Rede</TabsTrigger>
          <TabsTrigger value="queue" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6">Fila</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="mt-0 border-none p-0 focus-visible:ring-0"><WarRoomOverview /></TabsContent>
        <TabsContent value="forensic" className="mt-0 border-none p-0 focus-visible:ring-0"><ForensicTab /></TabsContent>
        <TabsContent value="targets" className="mt-0 border-none p-0 focus-visible:ring-0"><TargetsTab /></TabsContent>
        <TabsContent value="dossiers" className="mt-0 border-none p-0 focus-visible:ring-0"><DossiersTab /></TabsContent>
        <TabsContent value="alerts" className="mt-0 border-none p-0 focus-visible:ring-0"><AlertsTab /></TabsContent>
        <TabsContent value="network" className="mt-0 border-none p-0 focus-visible:ring-0"><NetworkTab /></TabsContent>
        <TabsContent value="queue" className="mt-0 border-none p-0 focus-visible:ring-0"><QueueTab /></TabsContent>
      </Tabs>
    </div>
  );
}
