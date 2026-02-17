import { supabase } from './supabase';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function getAuthHeaders() {
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;

    return {
        'Authorization': `Bearer ${token}`,
    };
}

export const apiService = {
    async uploadFile(file: File) {
        const headers = await getAuthHeaders();
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/ingest`, {
            method: 'POST',
            headers: {
                ...headers,
                // Content-Type is set automatically by fetch when using FormData
            },
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to upload file');
        }


        return await response.json();
    },

    async *streamChat(message: string, threadId: string) {
        const headers = await getAuthHeaders();

        const response = await fetch(`${API_BASE_URL}/chat/stream`, {
            method: 'POST',
            headers: {
                ...headers,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                thread_id: threadId,
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to start chat stream');
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error('No reader available');

        const decoder = new TextDecoder();
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        yield data;
                    } catch (e) {
                        console.error('Error parsing stream chunk', e);
                    }
                }
            }
        }
    },

    async clearUserData() {
        const headers = await getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            headers,
        });

        if (!response.ok) {
            throw new Error('Failed to clear user data');
        }

        return await response.json();
    },

    async approveRequest(threadId: string, approve: boolean, supervisorId: string, userId: string, editedResponse?: string) {
        const headers = await getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/approve`, {
            method: 'POST',
            headers: {
                ...headers,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                thread_id: threadId,
                approve,
                supervisor_id: supervisorId,
                user_id: userId,
                edited_response: editedResponse
            }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Approval failed');
        }

        return await response.json();
    }
};
