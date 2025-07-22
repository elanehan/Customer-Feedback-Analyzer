import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

type TopicData = {
  name: string;
  rank: number;
  type: 'positive' | 'negative';
};

interface TopicsBarChartProps {
  data: TopicData[];
}

export const TopicsBarChart = ({ data }: TopicsBarChartProps) => {
  if (!data || data.length === 0) return <div>No topic data available.</div>;

  const positiveData = data.filter(d => d.type === 'positive');
  const negativeData = data.filter(d => d.type === 'negative');

  return (
    // 2. Render two separate chart sections
    <div style={{ width: '100%' }}>
      {/* Positive Topics Chart */}
      <div>
        <h3 className="text-lg font-semibold text-slate-600 mb-2">Top Positive Topics</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart layout="vertical" data={positiveData} margin={{ top: 5, right: 30, left: 30, bottom: 5 }}>
            <XAxis type="number" dataKey="rank" domain={[0, 5]} hide />
            <YAxis dataKey="name" type="category" width={120} />
            <Tooltip />
            <Bar dataKey="rank" name="Importance Rank" fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Negative Topics Chart */}
      <div className="mt-6">
        <h3 className="text-lg font-semibold text-slate-600 mb-2">Top Negative Topics</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart layout="vertical" data={negativeData} margin={{ top: 5, right: 30, left: 30, bottom: 5 }}>
            <XAxis type="number" dataKey="rank" domain={[0, 5]} hide />
            <YAxis dataKey="name" type="category" width={120} />
            <Tooltip />
            <Bar dataKey="rank" name="Importance Rank" fill="#FF8042" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};