import { CommonModule } from '@angular/common';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ChatService } from './chat.service';
import { ChatTurn } from './chat.models';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss',
})
export class ChatComponent {
  @ViewChild('scrollAnchor') scrollAnchor?: ElementRef<HTMLDivElement>;

  messages: ChatTurn[] = [];
  draft = '';
  loading = false;
  error: string | null = null;

  readonly examples = [
    'What was the total spend per fiscal year?',
    'Top 10 suppliers by total spend',
    'How much did the state spend on IT Goods?',
    'Which departments made the most purchases?',
  ];

  constructor(private chat: ChatService) {}

  useExample(text: string): void {
    this.draft = text;
    this.send();
  }

  send(): void {
    const message = this.draft.trim();
    if (!message || this.loading) {
      return;
    }

    this.error = null;
    this.messages.push({ role: 'user', content: message });
    this.draft = '';
    this.loading = true;
    this.scrollSoon();

    // Send prior turns (exclude the message we just added) as history.
    const history = this.messages.slice(0, -1);

    this.chat.ask(message, history).subscribe({
      next: (res) => {
        this.messages.push({ role: 'assistant', content: res.answer });
        this.loading = false;
        this.scrollSoon();
      },
      error: (err) => {
        this.loading = false;
        this.error =
          err?.error?.detail ??
          'Could not reach the assistant. Is the backend running on :8000?';
        this.scrollSoon();
      },
    });
  }

  private scrollSoon(): void {
    setTimeout(() => {
      this.scrollAnchor?.nativeElement.scrollIntoView({ behavior: 'smooth' });
    });
  }
}
