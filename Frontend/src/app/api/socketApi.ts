export default class SocketApi {
    socket: WebSocket | null;

    constructor() {
        this.socket = null;
    }

    connect(url: string): void {
        if (this.socket) return;
        this.socket = new WebSocket(url);
    }

    disconnect(): void {
        if (!this.socket) return;
        this.socket.close();
        this.socket = null;
    }

    send(data: any): void {
        if (!this.socket) return;
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
