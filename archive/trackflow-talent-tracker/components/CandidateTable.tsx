import React from 'react';
import type { RecordOut } from '../types';
import { CandidateRow } from './CandidateRow';

export function CandidateTable({ candidates }: { candidates: RecordOut[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Position</th>
          <th>Status</th>
          <th>Stage</th>
        </tr>
      </thead>
      <tbody>
        {candidates.map((c) => (
          <CandidateRow key={c.id} candidate={c} />
        ))}
      </tbody>
    </table>
  );
}
