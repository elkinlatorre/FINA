"use client";

import React from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell
} from 'recharts';
import { TrendingUp, PieChart as PieIcon, ArrowUpRight, DollarSign } from 'lucide-react';

const performanceData = [
    { name: 'Jan', value: 4000 },
    { name: 'Feb', value: 3000 },
    { name: 'Mar', value: 5000 },
    { name: 'Apr', value: 4500 },
    { name: 'May', value: 6000 },
    { name: 'Jun', value: 7500 },
];

const allocationData = [
    { name: 'S&P 500', value: 45, color: '#3b82f6' },
    { name: 'Crypto', value: 25, color: '#8b5cf6' },
    { name: 'Bonds', value: 20, color: '#10b981' },
    { name: 'Cash', value: 10, color: '#f59e0b' },
];

export default function PortfolioOverview() {
    return (
        <div className="portfolio-container animate-fade-in p-8 overflow-y-auto h-full">
            <div className="grid grid-cols-4 gap-6 mb-8">
                <StatCard title="Total Value" value="$128,450" change="+12.5%" icon={<DollarSign size={20} />} />
                <StatCard title="Active Agents" value="4" change="Running" icon={<TrendingUp size={20} />} />
                <StatCard title="Knowledge" value="12 Docs" change="Ephemeral" icon={<ArrowUpRight size={20} />} />
                <StatCard title="Allocated" value="90%" change="Normal" icon={<PieIcon size={20} />} />
            </div>

            <div className="grid grid-cols-2 gap-8">
                <div className="glass-panel p-6 h-[400px]">
                    <h3 className="text-lg mb-6 flex items-center">
                        <TrendingUp size={18} className="mr-2 text-primary" /> Performance History
                    </h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={performanceData}>
                            <defs>
                                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                            <Tooltip
                                contentStyle={{ background: '#0d121b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px' }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Area type="monotone" dataKey="value" stroke="#3b82f6" fillOpacity={1} fill="url(#colorValue)" strokeWidth={3} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                <div className="glass-panel p-6 h-[400px]">
                    <h3 className="text-lg mb-6 flex items-center">
                        <PieIcon size={18} className="mr-2 text-secondary" /> Asset Allocation
                    </h3>
                    <div className="flex h-full items-center">
                        <ResponsiveContainer width="100%" height="80%">
                            <PieChart>
                                <Pie
                                    data={allocationData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={100}
                                    paddingAngle={8}
                                    dataKey="value"
                                >
                                    {allocationData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="allocation-legend flex flex-col gap-4">
                            {allocationData.map((item, idx) => (
                                <div key={idx} className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full" style={{ background: item.color }}></div>
                                    <span className="text-xs font-semibold">{item.name}</span>
                                    <span className="text-xs text-muted">{item.value}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <style jsx>{`
        .portfolio-container { max-width: 1200px; margin: 0 auto; }
      `}</style>
        </div>
    );
}

function StatCard({ title, value, change, icon }) {
    return (
        <div className="glass-panel p-6">
            <div className="flex justify-between items-start mb-4">
                <div className="text-primary bg-primary/10 p-2 rounded-lg">{icon}</div>
                <span className="text-xs font-bold text-secondary">{change}</span>
            </div>
            <h4 className="text-xs text-muted uppercase tracking-wider mb-1">{title}</h4>
            <p className="text-2xl font-bold">{value}</p>
        </div>
    )
}
