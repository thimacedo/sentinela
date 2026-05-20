'use client';

import DashboardStats from "./DashboardStats";
import ActivityChart from "./ActivityChart";

export default function WarRoomOverview() {
  return (
    <div className="space-y-6">
      <DashboardStats />
      <ActivityChart />
    </div>
  );
}
