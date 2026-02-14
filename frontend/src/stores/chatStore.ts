import { create } from 'zustand'
import { Message, Conversation } from '../types'

interface ChatState {
  conversations: Conversation[]
  currentConversation: Conversation | null
  messages: Message[]
  isConnected: boolean
  isTyping: boolean
  addMessage: (message: Message) => void
  setMessages: (messages: Message[]) => void
  setCurrentConversation: (conversation: Conversation | null) => void
  setConnected: (connected: boolean) => void
  setTyping: (typing: boolean) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isConnected: false,
  isTyping: false,
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  setMessages: (messages) => set({ messages }),
  setCurrentConversation: (conversation) => set({ currentConversation: conversation, messages: [] }),
  setConnected: (connected) => set({ isConnected: connected }),
  setTyping: (typing) => set({ isTyping: typing }),
  clearMessages: () => set({ messages: [] }),
}))
