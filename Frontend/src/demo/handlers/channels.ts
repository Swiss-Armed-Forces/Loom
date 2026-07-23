const subscriptions = new Map<WebSocket, Set<string>>();

export const addClient = (client: WebSocket): void => {
    subscriptions.set(client, new Set());
};

export const removeClient = (client: WebSocket): void => {
    subscriptions.delete(client);
};

export const subscribe = (client: WebSocket, channels: string[]): void => {
    const clientSubscriptions = subscriptions.get(client);
    channels.forEach((channel) => clientSubscriptions?.add(channel));
};

export const unsubscribe = (client: WebSocket, channels: string[]): void => {
    const clientSubscriptions = subscriptions.get(client);
    channels.forEach((channel) => clientSubscriptions?.delete(channel));
};

export const sendToChannel = (
    channel: string,
    message: Record<string, unknown>,
): void => {
    subscriptions.forEach((channels, client) => {
        if (channels.has(channel))
            client.send(JSON.stringify({ channel, message }));
    });
};

export const resetChannels = (): void => subscriptions.clear();
