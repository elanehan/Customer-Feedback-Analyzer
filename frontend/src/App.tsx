// import { useStream } from "@langchain/langgraph-sdk/react";
// import type { Message } from "@langchain/langgraph-sdk";
// import { useState, useEffect, useRef, useCallback } from "react";
// import { ProcessedEvent } from "@/components/ActivityTimeline";
// import { WelcomeScreen } from "@/components/WelcomeScreen";
// import { ChatMessagesView } from "@/components/ChatMessagesView";

// export default function App() {
//   const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
//     ProcessedEvent[]
//   >([]);
//   const [historicalActivities, setHistoricalActivities] = useState<
//     Record<string, ProcessedEvent[]>
//   >({});
//   const scrollAreaRef = useRef<HTMLDivElement>(null);
//   const hasFinalizeEventOccurredRef = useRef(false);

//   const thread = useStream<{
//     messages: Message[];
//     initial_search_query_count: number;
//     max_research_loops: number;
//     reasoning_model: string;
//   }>({
//     apiUrl: import.meta.env.DEV
//       ? "http://localhost:2024"
//       : "http://localhost:8123",
//     assistantId: "agent",
//     messagesKey: "messages",
//     onFinish: (event: any) => {
//       console.log(event);
//     },
//     onUpdateEvent: (event: any) => {
//       let processedEvent: ProcessedEvent | null = null;
//       if (event.generate_query) {
//         processedEvent = {
//           title: "Generating Search Queries",
//           data: event.generate_query.query_list.join(", "),
//         };
//       } else if (event.web_research) {
//         const sources = event.web_research.sources_gathered || [];
//         const numSources = sources.length;
//         const uniqueLabels = [
//           ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
//         ];
//         const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
//         processedEvent = {
//           title: "Web Research",
//           data: `Gathered ${numSources} sources. Related to: ${
//             exampleLabels || "N/A"
//           }.`,
//         };
//       } else if (event.reflection) {
//         processedEvent = {
//           title: "Reflection",
//           data: event.reflection.is_sufficient
//             ? "Search successful, generating final answer."
//             : `Need more information, searching for ${(event.reflection?.follow_up_queries ?? []).join(", ")}`,
//         };
//       } else if (event.finalize_answer) {
//         processedEvent = {
//           title: "Finalizing Answer",
//           data: "Composing and presenting the final answer.",
//         };
//         hasFinalizeEventOccurredRef.current = true;
//       }
//       if (processedEvent) {
//         setProcessedEventsTimeline((prevEvents) => [
//           ...prevEvents,
//           processedEvent!,
//         ]);
//       }
//     },
//   });

//   useEffect(() => {
//     if (scrollAreaRef.current) {
//       const scrollViewport = scrollAreaRef.current.querySelector(
//         "[data-radix-scroll-area-viewport]"
//       );
//       if (scrollViewport) {
//         scrollViewport.scrollTop = scrollViewport.scrollHeight;
//       }
//     }
//   }, [thread.messages]);

//   useEffect(() => {
//     if (
//       hasFinalizeEventOccurredRef.current &&
//       !thread.isLoading &&
//       thread.messages.length > 0
//     ) {
//       const lastMessage = thread.messages[thread.messages.length - 1];
//       if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
//         setHistoricalActivities((prev) => ({
//           ...prev,
//           [lastMessage.id!]: [...processedEventsTimeline],
//         }));
//       }
//       hasFinalizeEventOccurredRef.current = false;
//     }
//   }, [thread.messages, thread.isLoading, processedEventsTimeline]);

//   const handleSubmit = useCallback(
//     (submittedInputValue: string, effort: string, model: string) => {
//       if (!submittedInputValue.trim()) return;
//       setProcessedEventsTimeline([]);
//       hasFinalizeEventOccurredRef.current = false;

//       // convert effort to, initial_search_query_count and max_research_loops
//       // low means max 1 loop and 1 query
//       // medium means max 3 loops and 3 queries
//       // high means max 10 loops and 5 queries
//       let initial_search_query_count = 0;
//       let max_research_loops = 0;
//       switch (effort) {
//         case "low":
//           initial_search_query_count = 1;
//           max_research_loops = 1;
//           break;
//         case "medium":
//           initial_search_query_count = 3;
//           max_research_loops = 3;
//           break;
//         case "high":
//           initial_search_query_count = 5;
//           max_research_loops = 10;
//           break;
//       }

//       const newMessages: Message[] = [
//         ...(thread.messages || []),
//         {
//           type: "human",
//           content: submittedInputValue,
//           id: Date.now().toString(),
//         },
//       ];
//       thread.submit({
//         messages: newMessages,
//         initial_search_query_count: initial_search_query_count,
//         max_research_loops: max_research_loops,
//         reasoning_model: model,
//       });
//     },
//     [thread]
//   );

//   const handleCancel = useCallback(() => {
//     thread.stop();
//     window.location.reload();
//   }, [thread]);

//   return (
//     <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
//       <main className="flex-1 flex flex-col overflow-hidden max-w-4xl mx-auto w-full">
//         <div
//           className={`flex-1 overflow-y-auto ${
//             thread.messages.length === 0 ? "flex" : ""
//           }`}
//         >
//           {thread.messages.length === 0 ? (
//             <WelcomeScreen
//               handleSubmit={handleSubmit}
//               isLoading={thread.isLoading}
//               onCancel={handleCancel}
//             />
//           ) : (
//             <ChatMessagesView
//               messages={thread.messages}
//               isLoading={thread.isLoading}
//               scrollAreaRef={scrollAreaRef}
//               onSubmit={handleSubmit}
//               onCancel={handleCancel}
//               liveActivityEvents={processedEventsTimeline}
//               historicalActivities={historicalActivities}
//             />
//           )}
//         </div>
//       </main>
//     </div>
//   );
// }


import React, { useState, useEffect, useCallback } from 'react';
import { Input } from './components/ui/input';
import { Button } from './components/ui/button';
import mockData from './mock-data.json'; // Import our static mock data
import { SentimentPieChart } from './components/SentimentPieChart';
import { TopicsBarChart } from './components/TopicsBarChart';

// A helper function to process the raw API data into a format for our charts
type ApiResponse = {
  status: string;
  result: {
    summary: string;
    details: {
      positive_percent: number;
      negative_percent: number;
      neutral_percent: number;
      product_id: string;
      top_5_positive_topics: string[];
      top_5_negative_topics: string[];
    };
  };
};

const processApiData = (apiResponse: ApiResponse) => {
  if (!apiResponse || apiResponse.status !== 'completed') {
    return null;
  }
  
  const stats = apiResponse.result.details;

  // Process Sentiment Data for the Pie Chart
  const sentimentChartData = [
    { name: 'Positive' as const, value: stats.positive_percent },
    { name: 'Negative' as const, value: stats.negative_percent },
    { name: 'Neutral' as const, value: stats.neutral_percent }
  ]

  // Process Topic Data for the Bar Chart
  const positiveTopics = stats.top_5_positive_topics.map((name, index) => ({ name, rank: 5 - index, type: 'positive' as const }));
  const negativeTopics = stats.top_5_negative_topics.map((name, index) => ({ name, rank: 5 - index, type: 'negative' as const }));
  const topicChartData = [...positiveTopics, ...negativeTopics];

  return {
    summary: apiResponse.result.summary,
    sentimentChartData,
    topicChartData,
  };
};


type Analysis = {
  summary: string;
  sentimentChartData: { name: "Positive" | "Negative" | "Neutral"; value: number }[];
  topicChartData: { name: string; rank: number; type: 'positive' | 'negative' }[];
};

function App() {
  // We use useState to hold the processed data
  const [productId, setProductId] = useState<string>(""); // For the input field
  const [jobId, setJobId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(
    processApiData(mockData as ApiResponse)
  );

  const startAnalysis = useCallback(async () => {
    if (!productId) {
      setError("Please enter a Product ID.");
      return;
    }
    setIsLoading(true);
    setError(null);
    setAnalysis(null); // Clear previous results

    try {
      // The vite.config.ts proxy will forward this to http://127.0.0.1:8000/analyze
      const response = await fetch("/api/analyze", { 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: productId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to start analysis. Server responded with ${response.status}.`);
      }

      const data = await response.json();
      setJobId(data.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred.");
      setIsLoading(false);
    }
  }, [productId]);

  // This useEffect hook runs once when the component loads
  useEffect(() => {
    if (!jobId) return;

    const intervalId = setInterval(async () => {
      try {
        const response = await fetch(`/api/status/${jobId}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch job status. Server responded with ${response.status}.`);
        }
        const data = await response.json();

        if (data.status === 'completed') {
          clearInterval(intervalId);
          const processedData = processApiData(data);
          setAnalysis(processedData);
          setIsLoading(false);
          setJobId(null);
        } else if (data.status === 'failed') {
          clearInterval(intervalId);
          setError("Analysis job failed. Please check the backend logs for details.");
          setIsLoading(false);
          setJobId(null);
        }
      } catch (err) {
        clearInterval(intervalId);
        setError(err instanceof Error ? err.message : "An unknown error occurred while polling.");
        setIsLoading(false);
        setJobId(null);
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(intervalId); // Cleanup when component unmounts or jobId changes
  }, [jobId]);

  return (
    <div className="bg-slate-100 min-h-screen p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-slate-800">Customer Feedback Analyzer</h1>
          <p className="text-slate-600 mt-2">AI-powered insights from user reviews</p>
        </header>

        {/* We'll add the input section here later */}
        <div className="bg-white p-6 rounded-lg shadow mb-8">
          <div className="flex flex-col sm:flex-row gap-4">
            <Input
              type="text"
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              placeholder="Enter Product ID (e.g., B007JFMH8M)"
              disabled={isLoading}
              className="flex-grow"
            />
            <Button onClick={startAnalysis} disabled={isLoading} className="sm:w-auto w-full">
              {isLoading ? "Analyzing..." : "Analyze Product"}
            </Button>
          </div>
          {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
        </div>

        {analysis ? (
          <main className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:items-start">
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold text-slate-700 mb-4">Sentiment Distribution</h2>
                <SentimentPieChart data={analysis.sentimentChartData} />
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold text-slate-700 mb-4">Top 10 Topics</h2>
                <TopicsBarChart data={analysis.topicChartData} />
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold text-slate-700 mb-2">AI-Generated Summary</h2>
              <p className="text-slate-600 prose">{analysis.summary}</p>
            </div>
          </main>
        ) : (
          <div className="text-center text-slate-500">Loading analysis...</div>
        )}
      </div>
    </div>
  );
}

export default App;