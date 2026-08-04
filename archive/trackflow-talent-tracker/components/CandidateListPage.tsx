"use client";
import React, { useState } from 'react';
import { useCandidates } from '../hooks/useCandidates';
import { CandidateTable } from '../components/CandidateTable';

export default function CandidateListPage() {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [stage, setStage] = useState('');
  const { candidates, loading, error } = useCandidates({ search, status, stage });

  return (
    <div>
      <h1>Candidate List</h1>
      <div>
        <input
          placeholder="Search by name or email"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="received">Received</option>
          <option value="in_progress">In progress</option>
          <option value="selected">Selected</option>
          <option value="discarded">Discarded</option>
        </select>
        <select value={stage} onChange={(e) => setStage(e.target.value)}>
          <option value="">All Stages</option>
          <option value="pending">Pending review</option>
          <option value="review">Under review</option>
          <option value="personal_interview">Personal interview</option>
          <option value="technical_interview">Technical interview</option>
          <option value="offer_presented">Offer presented</option>
        </select>
      </div>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <CandidateTable candidates={candidates} />
    </div>
  );
}
