import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';

type TopicData = {
  name: string;
  count: number;
};

interface TopicsBarChartProps {
  data: TopicData[];
}

export const TopicsBarChart = ({ data }: TopicsBarChartProps) => {
  if (!data || data.length === 0) return <div>No topic data available.</div>;

  return (
    <div style={{ width: '100%', height: 500 }}>
      <ResponsiveContainer>
        <BarChart
          layout="vertical"
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis dataKey="name" type="category" width={100}/>
          <Tooltip />
          <Legend />
          <Bar dataKey="count" fill="#8884d8" name="Frequency"/>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};