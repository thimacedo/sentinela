'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import WarRoomOverview from "@/components/warroom/WarRoomOverview";
import ForensicTab from "@/components/warroom/ForensicTab";
import TargetsTab from "@/components/warroom/TargetsTab";
import DossiersTab from "@/components/warroom/DossiersTab";
import AlertsTab from "@/components/warroom/AlertsTab";
import NetworkTab from "@/components/warroom/NetworkTab";
import QueueTab from "@/components/warroom/QueueTab";

export default function WarRoom() {
  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-tactical-accent tracking-tighter">WAR ROOM</h1>
        <div className="text-right">
          <div className="text-[10px] font-mono text-tactical-accent/60 leading-none">
            SISTEMA SENTINELA // PASA v52.4
          </div>
          <div className="text-[8px] font-mono text-gray-500 uppercase tracking-widest mt-1">
            Central de Comando Operacional
          </div>
        </div>
      </div>
      
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="bg-black/50 border border-tactical-accent/20 p-1 mb-8 overflow-x-auto flex-nowrap justify-start rounded-none">
          <TabsTrigger value="overview" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6 border-r border-tactical-accent/10">Panorama</TabsTrigger>
          <TabsTrigger value="forensic" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6 border-r border-tactical-accent/10">Perícia</TabsTrigger>
          <TabsTrigger value="targets" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6 border-r border-tactical-accent/10">Alvos</TabsTrigger>
          <TabsTrigger value="alerts" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6 border-r border-tactical-accent/10">Alertas</TabsTrigger>
          <TabsTrigger value="network" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6 border-r border-tactical-accent/10">Rede</TabsTrigger>
          <TabsTrigger value="queue" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6 border-r border-tactical-accent/10">Workers</TabsTrigger>
          <TabsTrigger value="dossiers" className="data-[state=active]:bg-tactical-accent data-[state=active]:text-black rounded-none transition-all uppercase text-[10px] font-bold px-6">Dossiês</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="mt-0 border-none p-0 focus-visible:ring-0 animate-in fade-in duration-500">
          <WarRoomOverview />
        </TabsContent>
        <TabsContent value="forensic" className="mt-0 border-none p-0 focus-visible:ring-0 animate-in slide-in-from-left-4 duration-300">
          <ForensicTab />
        </TabsContent>
        <TabsContent value="targets" className="mt-0 border-none p-0 focus-visible:ring-0 animate-in slide-in-from-left-4 duration-300">
          <TargetsTab />
        </TabsContent>
        <TabsContent value="alerts" className="mt-0 border-none p-0 focus-visible:ring-0 animate-in slide-in-from-left-4 duration-300">
          <AlertsTab />
        </TabsContent>
        <TabsContent value="network" className="mt-0 border-none p-0 focus-visible:ring-0 animate-in slide-in-from-left-4 duration-300">
          <NetworkTab />
        </TabsContent>
        <TabsContent value="queue" className="mt-0 border-none p-0 focus-visible:ring-0 animate-in slide-in-from-left-4 duration-300">
          <QueueTab />
        </TabsContent>
        <TabsContent value="dossiers" className="mt-0 border-none p-0 focus-visible:ring-0 animate-in slide-in-from-left-4 duration-300">
          <DossiersTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
