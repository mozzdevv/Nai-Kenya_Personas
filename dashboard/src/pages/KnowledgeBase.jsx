import React, { useState, useEffect } from 'react';
import api from '../api';

const KnowledgeBase = () => {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const resp = await api.get('/knowledge?limit=100');
            setItems(Array.isArray(resp.data) ? resp.data : []);
            setLoading(false);
        } catch (error) {
            console.error('Failed to fetch knowledge base:', error);
            setItems([]);
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <header>
                <h1 className="text-3xl font-bold tracking-tight text-secondary-900">
                    Knowledge Base <span className="text-lg font-normal text-secondary-500">({items.length} items)</span>
                </h1>
                <p className="mt-2 text-lg text-secondary-600">
                    Source material used for RAG generation (from seed accounts).
                </p>
            </header>

            <div className="bg-white rounded-xl shadow-sm border border-secondary-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-secondary-200">
                        <thead className="bg-secondary-50">
                            <tr>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                                    Source Account
                                </th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                                    Content / Tweet
                                </th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                                    Topics
                                </th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wider">
                                    Ingested At
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-secondary-200">
                            {items.map((item) => (
                                <tr key={item.id} className="hover:bg-secondary-50 transition-colors duration-150">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-primary-600">
                                        @{item.source}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-secondary-900 max-w-xl truncate">
                                        {item.content}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-500">
                                        <div className="flex flex-wrap gap-1">
                                            {item.topics && item.topics.map((topic, i) => (
                                                <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-secondary-100 text-secondary-800">
                                                    {topic}
                                                </span>
                                            ))}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-500">
                                        {new Date(item.created_at).toLocaleString()}
                                    </td>
                                </tr>
                            ))}
                            {items.length === 0 && !loading && (
                                <tr>
                                    <td colSpan="4" className="px-6 py-12 text-center text-sm text-secondary-500">
                                        No knowledge base items found. Run the "Refresh RAG" script to populate.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default KnowledgeBase;
