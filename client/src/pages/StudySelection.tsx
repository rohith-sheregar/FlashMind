import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, BookOpen, BrainCircuit } from "lucide-react";
import { getDecks } from "../services/api";

interface Deck {
    id: number;
    request_id: string;
    title: string;
    card_count: number;
}

const StudySelection = () => {
    const [decks, setDecks] = useState<Deck[]>([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        fetchDecks();
    }, []);

    const fetchDecks = async () => {
        try {
            const fetchedDecks = await getDecks();
            setDecks(fetchedDecks);
        } catch (error) {
            console.error("Failed to fetch decks:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center mb-8">
                    <Link to="/" className="text-slate-500 hover:text-indigo-600 mr-4">
                        <ArrowLeft size={24} />
                    </Link>
                    <h1 className="text-3xl font-bold text-slate-800">Select a Deck to Study</h1>
                </div>

                {loading ? (
                    <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                        <p className="text-slate-500">Loading your library...</p>
                    </div>
                ) : decks.length === 0 ? (
                    <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-slate-200">
                        <BookOpen size={48} className="mx-auto text-slate-300 mb-4" />
                        <h3 className="text-xl font-medium text-slate-700 mb-2">No Decks Found</h3>
                        <p className="text-slate-500 mb-6">Upload a document to generate your first flashcard deck.</p>
                        <Link
                            to="/"
                            className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                        >
                            Go to Upload
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {decks.map((deck) => (
                            <div
                                key={deck.id}
                                onClick={() => navigate(`/study/${deck.request_id}`)}
                                className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:shadow-md hover:border-indigo-200 transition-all cursor-pointer group"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="p-3 bg-indigo-50 rounded-lg group-hover:bg-indigo-100 transition-colors">
                                        <BrainCircuit className="text-indigo-600" size={24} />
                                    </div>
                                    <span className="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-1 rounded-full">
                                        {deck.card_count} Cards
                                    </span>
                                </div>
                                <h3 className="font-semibold text-slate-800 mb-2 line-clamp-2 group-hover:text-indigo-600 transition-colors">
                                    {deck.title}
                                </h3>
                                <p className="text-sm text-slate-500">Click to start studying</p>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default StudySelection;
