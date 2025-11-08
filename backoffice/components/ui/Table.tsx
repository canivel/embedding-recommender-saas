import React from 'react';

interface TableProps {
  children: React.ReactNode;
  className?: string;
}

export const Table: React.FC<TableProps> = ({ children, className = '' }) => (
  <div className="overflow-x-auto">
    <table className={`w-full border-collapse ${className}`}>{children}</table>
  </div>
);

interface TableHeaderProps {
  children: React.ReactNode;
}

export const TableHeader: React.FC<TableHeaderProps> = ({ children }) => (
  <thead className="bg-gray-50 border-b-2 border-gray-200">
    {children}
  </thead>
);

interface TableBodyProps {
  children: React.ReactNode;
}

export const TableBody: React.FC<TableBodyProps> = ({ children }) => (
  <tbody className="divide-y divide-gray-200">{children}</tbody>
);

interface TableRowProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export const TableRow: React.FC<TableRowProps> = ({ children, className = '', hover = true }) => (
  <tr className={`${hover ? 'hover:bg-gray-50' : ''} ${className}`}>{children}</tr>
);

interface TableCellProps {
  children: React.ReactNode;
  className?: string;
  header?: boolean;
  align?: 'left' | 'center' | 'right';
}

export const TableCell: React.FC<TableCellProps> = ({
  children,
  className = '',
  header = false,
  align = 'left',
}) => {
  const alignClass = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  }[align];

  return header ? (
    <th className={`px-6 py-3 font-semibold text-gray-700 ${alignClass} ${className}`}>
      {children}
    </th>
  ) : (
    <td className={`px-6 py-4 text-gray-900 ${alignClass} ${className}`}>{children}</td>
  );
};
