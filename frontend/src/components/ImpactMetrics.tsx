import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

interface ImpactMetricsProps {
  data: {
    name: string;
    value: number;
    color: string;
  }[];
  riskDistribution: {
    tier: string;
    count: number;
    impact: number;
  }[];
}

export const ImpactMetrics = ({ data, riskDistribution }: ImpactMetricsProps) => {
  return (
    <div className="glass-panel section-card" style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
      <div>
        <h3 className="section-title" style={{ marginBottom: 20, fontSize: 16, color: 'var(--text-secondary)' }}>Risk Distribution</h3>
        <div style={{ height: 220, width: '100%' }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                innerRadius={60}
                outerRadius={84}
                paddingAngle={6}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                ))}
              </Pie>
              <Tooltip
                cursor={{ fill: 'transparent' }}
                contentStyle={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', borderRadius: 12 }}
                itemStyle={{ color: '#fff' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12, marginTop: 18 }}>
          {data.map((item) => (
            <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: item.color }} />
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{item.name}: {item.value}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="section-title" style={{ marginBottom: 20, fontSize: 16, color: 'var(--text-secondary)' }}>Fan-Out Impact Score</h3>
        <div style={{ height: 220, width: '100%' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={riskDistribution}>
              <XAxis dataKey="tier" stroke="var(--text-tertiary)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="var(--text-tertiary)" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip
                cursor={{ fill: 'var(--bg-secondary)' }}
                contentStyle={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', borderRadius: 12 }}
              />
              <Bar dataKey="impact" radius={[4, 4, 0, 0]}>
                {riskDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={
                    entry.tier === 'Critical' ? '#ff4d4f' :
                    entry.tier === 'High' ? '#faad14' :
                    entry.tier === 'Medium' ? '#1890ff' :
                    '#52c41a'
                  } />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
