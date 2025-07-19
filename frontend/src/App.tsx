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


import React, { useState, useEffect } from 'react';
import mockData from './mock-data.json'; // Import our static mock data
import { SentimentPieChart } from './components/SentimentPieChart';
import { TopicsBarChart } from './components/TopicsBarChart';

// A helper function to process the raw API data into a format for our charts
type ApiResponse = {
  status: string;
  result: {
    summary: string;
    details: {
      rating: number;
      sentiment: 'Positive' | 'Negative' | 'Neutral';
      topics: string[];
      review_timestamp: string;
    }[];
  };
};

const processApiData = (apiResponse: ApiResponse) => {
  if (!apiResponse || apiResponse.status !== 'completed') {
    return null;
  }
  
  const analysisList = apiResponse.result.details;

  // 1. Process Sentiment Data
  const sentimentCounts = { Positive: 0, Negative: 0, Neutral: 0 };
  analysisList.forEach(item => {
    if (item.sentiment in sentimentCounts) {
      sentimentCounts[item.sentiment]++;
    }
  });
  const sentimentChartData = Object.entries(sentimentCounts).map(
    ([name, value]) => ({
      name: name as "Positive" | "Negative" | "Neutral",
      value,
    })
  );

  // 2. Process Topic Data
  const topicCounts: Record<string, number> = {};
  analysisList.forEach(item => {
    item.topics.forEach(topic => {
      topicCounts[topic] = (topicCounts[topic] || 0) + 1;
    });
  });
  const topicChartData = Object.entries(topicCounts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count) // Sort topics by frequency
    .slice(0, 10); // Show top 10 topics

  return {
    summary: apiResponse.result.summary,
    sentimentChartData,
    topicChartData,
    totalReviews: analysisList.length
  };
};


type Analysis = {
  summary: string;
  sentimentChartData: { name: "Positive" | "Negative" | "Neutral"; value: number }[];
  topicChartData: { name: string; count: number }[];
  totalReviews: number;
};

function App() {
  // We use useState to hold the processed data
  const [analysis, setAnalysis] = useState<Analysis | null>(null);

  // This useEffect hook runs once when the component loads
  useEffect(() => {
    try {
      console.log("--- DEBUGGING useEffect ---");
      
      // 1. Check the raw imported data
      console.log("1. Raw imported mockData:", mockData);
      if (!mockData) {
        throw new Error("mockData object is null or undefined. Check the file path and content.");
      }

      // 2. Call the processing function
      console.log("2. Calling processApiData with the mock data...");
      const processedData = processApiData(mockData as ApiResponse);
      
      // 3. Check the result of the processing function
      console.log("3. Data after processing:", processedData);
      if (!processedData) {
        throw new Error("processApiData function returned null. Check for a logic error inside it.");
      }

      // 4. Set the state
      console.log("4. Calling setAnalysis with the processed data.");
      setAnalysis(processedData);
      console.log("5. State has been set. The dashboard should now render.");

    } catch (error) {
      console.error("❌ An error occurred inside the useEffect hook:", error);
    }
  }, []); // The empty dependency array means this runs only once on mount

  return (
    <div className="bg-slate-100 min-h-screen p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-slate-800">Customer Feedback Analyzer</h1>
          <p className="text-slate-600 mt-2">AI-powered insights from user reviews</p>
        </header>

        {/* We'll add the input section here later */}

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