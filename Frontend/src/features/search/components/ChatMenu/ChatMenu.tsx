import { Chatbot } from "./Chatbot";

interface ChatMenuProps {
    isOpen: boolean;
    toggleMenu: () => void;
}

export const ChatMenu = ({ isOpen }: ChatMenuProps) => {
    return <>{isOpen && <Chatbot />}</>;
};
