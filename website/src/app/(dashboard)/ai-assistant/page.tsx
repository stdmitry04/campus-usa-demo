// ===== website/src/app/(dashboard)/ai-assistant/page.tsx (COMPLETE VERSION) =====
'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useMessaging } from '@/hooks/useMessaging';
import { useAuth } from '@/context/AuthContext';
import PageHeader from '@/components/layout/PageHeader';
import {
    BsSend,
    BsExclamationTriangle,
    BsArrowLeft,
    BsTrash,
    BsPlus,
    BsRobot,
    BsPerson
} from 'react-icons/bs';

export default function AIAssistantPage() {
    const [message, setMessage] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { user } = useAuth();

    const {
        conversations,
        currentConversation,
        currentMessages,
        loading,
        sending,
        error,
        sendMessage,
        fetchConversation,
        startNewConversation,
        deleteConversation,
        setError
    } = useMessaging();

    // auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [currentMessages]);

    // handle sending a message
    const handleSendMessage = useCallback(async () => {
        if (!message.trim() || sending) return;

        const messageToSend = message;
        setMessage(''); // clear input immediately

        try {
            const response = await sendMessage(messageToSend, currentConversation?.id);

            // if this is a new conversation, switch to it
            if (!currentConversation && response.conversation_id) {
                await fetchConversation(response.conversation_id);
            }
        } catch (error) {
            console.log('failed to send message:', error);
            setMessage(messageToSend); // restore message on error
        }
    }, [message, sending, sendMessage, currentConversation, fetchConversation]);

    // handle key press in input
    const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    }, [handleSendMessage]);

    // handle conversation selection
    const handleConversationSelect = useCallback(async (conversationId: string) => {
        try {
            await fetchConversation(conversationId);
        } catch (error) {
            console.log('failed to load conversation:', error);
        }
    }, [fetchConversation]);

    // handle conversation deletion
    const handleDeleteConversation = useCallback(async (conversationId: string) => {
        if (!confirm('are you sure you want to delete this conversation?')) return;

        try {
            await deleteConversation(conversationId);
        } catch (error) {
            console.log('failed to delete conversation:', error);
        }
    }, [deleteConversation]);

    // handle quick start messages
    const handleQuickStart = useCallback((quickMessage: string) => {
        setMessage(quickMessage);
    }, []);

    // format message timestamp
    const formatTime = (timestamp: string) => {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // quick start questions
    const quickStartQuestions = [
        "What are MIT's computer science requirements?",
        "How do I apply for an F-1 student visa?",
        "Which universities give financial aid to international students?",
        "What SAT score do I need for top universities?",
        "How do I write a good college essay?",
        "What documents do I need for university applications?"
    ];

    return (
        <>
            <PageHeader title="AI Assistant" />

            {/* error display */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start">
                    <BsExclamationTriangle className="text-red-500 h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <div className="text-red-800 font-medium">error</div>
                        <div className="text-red-600 text-sm">{error}</div>
                    </div>
                    <button
                        onClick={() => setError(null)}
                        className="ml-auto text-red-400 hover:text-red-600"
                    >
                        ×
                    </button>
                </div>
            )}

            <div className="flex bg-white rounded-lg shadow-sm border border-gray-200 h-[80vh]">
                {/* conversations sidebar */}
                <div className="w-80 border-r border-gray-200 flex flex-col">
                    <div className="p-4 border-b border-gray-200">
                        <button
                            onClick={startNewConversation}
                            className="w-full flex items-center justify-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            <BsPlus className="h-4 w-4 mr-2" />
                            new conversation
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto">
                        {loading && conversations.length === 0 ? (
                            <div className="p-4 text-center text-gray-500">loading conversations...</div>
                        ) : conversations.length === 0 ? (
                            <div className="p-4 text-center text-gray-500">
                                <div className="text-4xl mb-2">💬</div>
                                <div className="text-sm">no conversations yet</div>
                                <div className="text-xs text-gray-400 mt-1">
                                    start chatting to create your first conversation!
                                </div>
                            </div>
                        ) : (
                            conversations.map((conv) => (
                                <div
                                    key={conv.id}
                                    className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors ${
                                        currentConversation?.id === conv.id ? 'bg-blue-50 border-r-2 border-r-blue-600' : ''
                                    }`}
                                    onClick={() => handleConversationSelect(conv.id)}
                                >
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1 min-w-0">
                                            <h4 className="text-sm font-medium text-gray-900 truncate">
                                                {conv.title || 'new conversation'}
                                            </h4>
                                            <p className="text-xs text-gray-500 mt-1">
                                                {conv.message_count} messages
                                            </p>
                                            <p className="text-xs text-gray-400">
                                                {new Date(conv.updated_at).toLocaleDateString()}
                                            </p>
                                        </div>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteConversation(conv.id);
                                            }}
                                            className="ml-2 text-gray-400 hover:text-red-600 p-1 transition-colors"
                                        >
                                            <BsTrash className="h-3 w-3" />
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* chat area */}
                <div className="flex-1 flex flex-col">
                    {currentConversation ? (
                        <>
                            {/* chat header */}
                            <div className="p-4 border-b border-gray-200 bg-gray-50">
                                <div className="flex items-center">
                                    <button
                                        onClick={startNewConversation}
                                        className="lg:hidden mr-3 text-gray-400 hover:text-gray-600"
                                    >
                                        <BsArrowLeft className="h-5 w-5" />
                                    </button>
                                    <div className="flex items-center">
                                        <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                                            <BsRobot className="h-4 w-4 text-blue-600" />
                                        </div>
                                        <div>
                                            <h3 className="font-medium text-gray-900">{currentConversation.title}</h3>
                                            <p className="text-sm text-gray-500">
                                                {currentMessages.length} messages • AI college counselor
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* messages */}
                            <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
                                {currentMessages.length === 0 ? (
                                    <div className="flex items-center justify-center h-full">
                                        <div className="text-center text-gray-500">
                                            <div className="text-lg mb-2">👋</div>
                                            <div>start the conversation!</div>
                                        </div>
                                    </div>
                                ) : (
                                    currentMessages.map((msg, index) => (
                                        <div
                                            key={msg.id || index}
                                            className={`mb-6 flex ${
                                                msg.sender === 'user' ? 'justify-end' : 'justify-start'
                                            }`}
                                        >
                                            <div className={`max-w-[75%] ${msg.sender === 'user' ? 'order-2' : 'order-1'}`}>
                                                {/* avatar */}
                                                <div className={`flex items-center mb-2 ${
                                                    msg.sender === 'user' ? 'justify-end' : 'justify-start'
                                                }`}>
                                                    {msg.sender === 'assistant' ? (
                                                        <div className="h-6 w-6 bg-blue-100 rounded-full flex items-center justify-center mr-2">
                                                            <BsRobot className="h-3 w-3 text-blue-600" />
                                                        </div>
                                                    ) : (
                                                        <div className="h-6 w-6 bg-gray-200 rounded-full flex items-center justify-center ml-2">
                                                            <BsPerson className="h-3 w-3 text-gray-600" />
                                                        </div>
                                                    )}
                                                    <span className="text-xs text-gray-500 font-medium">
                                                        {msg.sender === 'user' ? (user?.first_name || 'You') : 'AI Assistant'}
                                                    </span>
                                                </div>

                                                {/* message bubble */}
                                                <div
                                                    className={`px-4 py-3 rounded-2xl shadow-sm ${
                                                        msg.sender === 'user'
                                                            ? 'bg-blue-600 text-white'
                                                            : 'bg-white text-gray-900 border border-gray-200'
                                                    }`}
                                                >
                                                    <div className="whitespace-pre-wrap text-sm leading-relaxed">
                                                        {msg.content}
                                                    </div>

                                                    {/* message metadata */}
                                                    <div className={`text-xs mt-2 ${
                                                        msg.sender === 'user' ? 'text-blue-100' : 'text-gray-400'
                                                    }`}>
                                                        {formatTime(msg.created_at)}
                                                        {msg.response_time && (
                                                            <span className="ml-2">
                                                                • {msg.response_time.toFixed(1)}s
                                                            </span>
                                                        )}
                                                        {msg.model_used && msg.sender === 'assistant' && (
                                                            <span className="ml-2">
                                                                • {msg.model_used}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}

                                {/* typing indicator */}
                                {sending && (
                                    <div className="flex justify-start mb-6">
                                        <div className="max-w-[75%]">
                                            <div className="flex items-center mb-2">
                                                <div className="h-6 w-6 bg-blue-100 rounded-full flex items-center justify-center mr-2">
                                                    <BsRobot className="h-3 w-3 text-blue-600" />
                                                </div>
                                                <span className="text-xs text-gray-500 font-medium">AI Assistant</span>
                                            </div>
                                            <div className="bg-white text-gray-900 px-4 py-3 rounded-2xl border border-gray-200 shadow-sm">
                                                <div className="flex items-center space-x-1">
                                                    <div className="flex space-x-1">
                                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                                    </div>
                                                    <span className="text-sm text-gray-500 ml-2">thinking...</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                <div ref={messagesEndRef} />
                            </div>
                        </>
                    ) : (
                        /* welcome screen */
                        <div className="flex-1 flex items-center justify-center p-6 bg-gray-50">
                            <div className="text-center max-w-2xl">
                                <div className="text-6xl mb-6">🎓</div>
                                <h2 className="text-2xl font-bold text-gray-900 mb-3">
                                    college application AI assistant
                                </h2>
                                <p className="text-gray-600 mb-8 text-lg">
                                    get personalized help with university applications, visa requirements,
                                    and document preparation for studying in the US
                                </p>

                                {/* capabilities */}
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8 text-sm">
                                    <div className="bg-white p-3 rounded-lg border border-gray-200">
                                        <div className="text-lg mb-1">🏫</div>
                                        <div className="font-medium">university selection</div>
                                    </div>
                                    <div className="bg-white p-3 rounded-lg border border-gray-200">
                                        <div className="text-lg mb-1">📋</div>
                                        <div className="font-medium">application deadlines</div>
                                    </div>
                                    <div className="bg-white p-3 rounded-lg border border-gray-200">
                                        <div className="text-lg mb-1">📊</div>
                                        <div className="font-medium">test requirements</div>
                                    </div>
                                    <div className="bg-white p-3 rounded-lg border border-gray-200">
                                        <div className="text-lg mb-1">🛂</div>
                                        <div className="font-medium">F-1 visa process</div>
                                    </div>
                                    <div className="bg-white p-3 rounded-lg border border-gray-200">
                                        <div className="text-lg mb-1">💰</div>
                                        <div className="font-medium">financial aid</div>
                                    </div>
                                    <div className="bg-white p-3 rounded-lg border border-gray-200">
                                        <div className="text-lg mb-1">✍️</div>
                                        <div className="font-medium">essay guidance</div>
                                    </div>
                                </div>

                                {/* quick start questions */}
                                <div className="text-left">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">💡 quick start questions:</h3>
                                    <div className="grid gap-2">
                                        {quickStartQuestions.map((question, index) => (
                                            <button
                                                key={index}
                                                onClick={() => handleQuickStart(question)}
                                                className="text-left p-3 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-sm"
                                            >
                                                {question}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* message input */}
                    <div className="border-t border-gray-200 p-4 bg-white">
                        <div className="flex items-center gap-3">
                            <div className="flex-1 relative">
                                <input
                                    type="text"
                                    value={message}
                                    onChange={(e) => setMessage(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    placeholder="ask me anything about college applications..."
                                    className="w-full py-3 px-4 pr-12 bg-gray-100 rounded-full border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white focus:border-blue-500 transition-colors"
                                    disabled={sending}
                                />
                                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 text-sm">
                                    {message.length}/500
                                </div>
                            </div>
                            <button
                                onClick={handleSendMessage}
                                disabled={!message.trim() || sending}
                                className="bg-blue-600 text-white p-3 rounded-full hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
                            >
                                {sending ? (
                                    <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                ) : (
                                    <BsSend className="h-5 w-5" />
                                )}
                            </button>
                        </div>

                        {/* helpful tip */}
                        <div className="mt-2 text-xs text-gray-500 text-center">
                            💡 tip: be specific about your academic background and goals for better advice
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}
