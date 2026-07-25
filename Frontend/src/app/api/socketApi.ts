export default class SocketApi {
    socket: WebSocket | null;
    // Messages sent before connect() is called are queued here and replayed
    // once the socket is created. This lets components subscribe to channels
    // during their mount effects without racing against the async WebSocket
    // setup in fetchInitialSearchState.
    private readonly preConnectQueue: any[] = [];

    constructor() {
        this.socket = null;
    }

    connect(url: string): void {
        if (this.socket) return;
        this.socket = new WebSocket(url);
        // Drain any messages that arrived before the socket was created. Each
        // call to send() below will use the existing readyState-based queuing
        // (addEventListener "open") if the handshake is still in progress.
        for (const data of this.preConnectQueue.splice(0)) {
            this.send(data);
        }
    }

    disconnect(): void {
        if (!this.socket) return;
        this.socket.close();
        this.socket = null;
        this.preConnectQueue.length = 0;
    }

    send(data: any): void {
        if (!this.socket) {
            this.preConnectQueue.push(data);
            return;
        }
        if (this.socket.readyState !== WebSocket.OPEN) {
            // Queue the message to be sent once the connection is established.
            this.socket.addEventListener(
                "open",
                () => this.socket?.send(JSON.stringify(data)),
                { once: true },
            );
            return;
        }
        this.socket.send(JSON.stringify(data));
    }

    on(eventName: string, callback: (data: any) => void): void {
        if (!this.socket) return;
        this.socket.addEventListener(eventName, callback);
    }
}
