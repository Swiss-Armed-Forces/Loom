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
        this.socket.send(JSON.stringify(data));
    }

    on(eventName: string, callback: (data: any) => void): void {
        if (!this.socket) return;
        this.socket.addEventListener(eventName, callback);
    }
}
