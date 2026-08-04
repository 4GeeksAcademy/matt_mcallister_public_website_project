import React from 'react';
import type { RecordOut } from '../types';
import Link from 'next/link';

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

export function CandidateRow({ candidate }: { candidate: RecordOut }) {
  return (
    <tr style={{ cursor: 'pointer' }}>
      <td>
        <Link href={`/candidates/${candidate.id}`}>{candidate.full_name}</Link>
      </td>
      <td>{candidate.position}</td>
      <td>{statusLabels[candidate.status]}</td>
      <td>{stageLabels[candidate.stage]}</td>
    </tr>
  );
}
