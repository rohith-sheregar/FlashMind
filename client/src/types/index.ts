export interface IFlashcard {
  id: string;
  question: string;
  answer: string;
  deck_id?: string; // Foreign key reference
}

export interface IDeck {
  id: string;
  title: string;
  created_at: string;
  cards: IFlashcard[];
}

export interface IUploadResponse {
  deck_id: string;
  message: string;
}
