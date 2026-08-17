import { Chatbot } from "./Chatbot";
import { useChatbot } from "./useChatbot";

interface ChatMenuProps {
    isOpen: boolean;
    toggleMenu: () => void;
    onCitationClick?: (fileId: string) => void;
}

export const ChatMenu = ({
    isOpen,
    onCitationClick = () => {},
}: ChatMenuProps) => {
    const chatbot = useChatbot(isOpen);
    return (
        <>
            {isOpen && (
                <Chatbot onCitationClick={onCitationClick} chatbot={chatbot} />
            )}
        </>
    );
};
