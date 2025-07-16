import { useStream } from '@langchain/langgraph-sdk/react';
import type { Message } from '@langchain/langgraph-sdk';
import { useState, useEffect, useRef, useCallback } from 'react';
import { ProcessedEvent } from '@/components/ActivityTimeline';
import { WelcomeScreen } from '@/components/WelcomeScreen';
import { ChatMessagesView } from '@/components/ChatMessagesView';
import { Button } from '@/components/ui/button';
import { initLangGraph } from './lib/utils';

export default function App() {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);
  const [error, setError] = useState<string | null>(null);

  const thread = useStream<{
    messages: Message[];
    persona: string;
    reasoning_model: string;
  }>({
    apiUrl: import.meta.env.DEV
      ? import.meta.env.VITE_APP_URL
      : import.meta.env.VITE_APP_URL_PROD,
    assistantId: 'agent',
    messagesKey: 'messages',
    onUpdateEvent: (event: any) => {
      console.log('event', event);
      let processedEvent: ProcessedEvent | null = null;
      if (event.analytic) {
        processedEvent = {
          title: 'Analytic',
          data: 'The query is routed to the analytic agent node',
        };
      } else if (event.rag) {
        processedEvent = {
          title: 'RAG',
          data: 'The query is routed to the RAG agent node',
        };
      } else if (event.format) {
        processedEvent = {
          title: 'Formatting',
          data: 'Composing and presenting the final answer.',
        };
        hasFinalizeEventOccurredRef.current = true;
      }

      if (processedEvent) {
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
        console.log('processedEventsTimeline', processedEvent);
      }
    },
    onError: (error: any) => {
      setError(error.message);
    },
  });

  useEffect(() => {
    initLangGraph();
  }, []);

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        '[data-radix-scroll-area-viewport]'
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [thread.messages]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      console.log('***thread.messages', thread.messages);
      const lastMessage = thread.messages[thread.messages.length - 1];
      if (lastMessage && lastMessage.type === 'ai' && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [thread.messages, thread.isLoading, processedEventsTimeline]);

  const handleSubmit = useCallback(
    (submittedInputValue: string, persona: string, model: string) => {
      if (!submittedInputValue.trim()) return;
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;

      const newMessages: Message[] = [
        ...[],
        {
          type: 'human',
          content: submittedInputValue,
          id: Date.now().toString(),
        },
      ];
      thread.submit({
        messages: newMessages,
        persona: persona,
        reasoning_model: model,
      });
    },
    [thread]
  );

  const handleCancel = useCallback(() => {
    thread.stop();
    window.location.reload();
  }, [thread]);

  return (
    <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
      <main className="h-full w-full max-w-4xl mx-auto">
        {thread.messages.length === 0 ? (
          <WelcomeScreen
            handleSubmit={handleSubmit}
            isLoading={thread.isLoading}
            onCancel={handleCancel}
          />
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="flex flex-col items-center justify-center gap-4">
              <h1 className="text-2xl text-red-400 font-bold">Error</h1>
              <p className="text-red-400">{JSON.stringify(error)}</p>

              <Button
                variant="destructive"
                onClick={() => window.location.reload()}
              >
                Retry
              </Button>
            </div>
          </div>
        ) : (
          <ChatMessagesView
            messages={
              thread.messages as (Message & { tool: 'rag' | 'analytic' })[]
            }
            isLoading={thread.isLoading}
            scrollAreaRef={scrollAreaRef}
            liveActivityEvents={processedEventsTimeline}
            historicalActivities={historicalActivities}
          />
        )}
      </main>
    </div>
  );
}
