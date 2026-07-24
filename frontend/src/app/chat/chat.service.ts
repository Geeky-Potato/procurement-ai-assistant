import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { ChatRequest, ChatResponse, ChatTurn } from './chat.models';

const API_BASE = 'http://localhost:8000';

@Injectable({ providedIn: 'root' })
export class ChatService {
  constructor(private http: HttpClient) {}

  ask(message: string, history: ChatTurn[]): Observable<ChatResponse> {
    const body: ChatRequest = { message, history };
    return this.http.post<ChatResponse>(`${API_BASE}/api/chat`, body);
  }
}
