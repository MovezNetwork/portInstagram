import { Script, Command, Response, CommandSystem, CommandUI } from './commands';
export interface ProcessingEngine {
    start: (script: Script) => void;
    commandHandler: CommandHandler;
    terminate: () => void;
}
export interface VisualisationEngine {
    start: (rootElement: HTMLElement, locale: string) => void;
    render: (command: CommandUI) => Promise<Response>;
    terminate: () => void;
}
export interface System {
    send: (command: CommandSystem) => void;
}
export interface CommandHandler {
    onCommand: (command: Command) => Promise<Response>;
}
