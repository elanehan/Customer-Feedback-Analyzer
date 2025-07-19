import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = {
  Positive: '#82ca9d', // Green
  Negative: '#FF8042', // Red
  Neutral: '#FFBB28',  // Yellow
};

type SentimentData = { name: keyof typeof COLORS; value: number };

interface SentimentPieChartProps {
  data: SentimentData[];
}

export const SentimentPieChart = ({ data }: SentimentPieChartProps) => {
  if (!data || data.length === 0) return <div>No sentiment data available.</div>;

  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
            nameKey="name"
            label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};