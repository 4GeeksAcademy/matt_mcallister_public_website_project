"use client";
import { useParams } from 'next/navigation';
import { useCandidate } from '../../../hooks/useCandidate';
import { useNotes } from '../../../hooks/useNotes';
import React from 'react';

const statusLabels: Record<string, string> = {
  received: 'Received',
  in_progress: 'In progress',
  selected: 'Selected',
  discarded: 'Discarded',
};

const stageLabels: Record<string, string> = {
  pending: 'Pending review',
  review: 'Under review',
  personal_interview: 'Personal interview',
  technical_interview: 'Technical interview',
  offer_presented: 'Offer presented',
};

export default function CandidateDetailPage() {
  const params = useParams();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  const { candidate, loading, error } = useCandidate(id);
  const { notes, loading: notesLoading, error: notesError } = useNotes(id);

  if (loading) return <p>Loading...</p>;
  if (error || !candidate) return <p style={{ color: 'red' }}>{error || 'Candidate not found'}</p>;

  return (
    <div>
      <h1>{candidate.full_name}</h1>
      <p><b>Email:</b> {candidate.email}</p>
      <p><b>Phone:</b> {candidate.phone}</p>
      <p><b>Position:</b> {candidate.position}</p>
      <p><b>Status:</b> {statusLabels[candidate.status]}</p>
      <p><b>Stage:</b> {stageLabels[candidate.stage]}</p>
      <p><b>Experience:</b> {candidate.experience_years} years</p>
      <p><b>LinkedIn:</b> {candidate.linkedin_url ? <a href={candidate.linkedin_url}>Profile</a> : 'N/A'}</p>
      <p><b>CV:</b> {candidate.cv_url ? <a href={candidate.cv_url}>Download</a> : 'N/A'}</p>
      <p><b>Applied at:</b> {candidate.applied_at}</p>
      <p><b>Updated at:</b> {candidate.updated_at}</p>
      <h2>Notes</h2>
      {notesLoading && <p>Loading notes...</p>}
      {notesError && <p style={{ color: 'red' }}>{notesError}</p>}
      <ul>
        {notes && notes.map((note) => (
          <li key={note.id}>{note.content}</li>
        ))}
      </ul>
    </div>
  );
}
