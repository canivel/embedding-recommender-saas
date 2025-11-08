import React from 'react';
import { clsx } from 'clsx';

// Generic table with columns and data
interface Column<T> {
  header: string;
  accessor: keyof T;
  render?: (value: any, row: T) => React.ReactNode;
}

interface TableProps<T = any> {
  columns: Column<T>[];
  data: T[];
  className?: string;
}

export function Table<T extends Record<string, any>>({ columns, data, className }: TableProps<T>) {
  return (
    <div className="overflow-x-auto">
      <table className={clsx('min-w-full divide-y divide-gray-200', className)}>
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column, idx) => (
              <th
                key={idx}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, rowIdx) => (
            <tr key={rowIdx} className="hover:bg-gray-50">
              {columns.map((column, colIdx) => (
                <td key={colIdx} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {column.render
                    ? column.render(row[column.accessor], row)
                    : String(row[column.accessor])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Composable table components
interface BaseTableProps {
  children: React.ReactNode;
  className?: string;
}

export function TableContainer({ children, className }: BaseTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className={clsx('min-w-full divide-y divide-gray-200', className)}>
        {children}
      </table>
    </div>
  );
}

export function TableHeader({ children, className }: BaseTableProps) {
  return (
    <thead className={clsx('bg-gray-50', className)}>
      {children}
    </thead>
  );
}

export function TableBody({ children, className }: BaseTableProps) {
  return (
    <tbody className={clsx('bg-white divide-y divide-gray-200', className)}>
      {children}
    </tbody>
  );
}

interface TableRowProps extends BaseTableProps {
  onClick?: () => void;
}

export function TableRow({ children, className, onClick }: TableRowProps) {
  return (
    <tr
      className={clsx(onClick && 'cursor-pointer hover:bg-gray-50', className)}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}

interface TableHeadProps extends BaseTableProps {
  sortable?: boolean;
  onSort?: () => void;
}

export function TableHead({ children, className, sortable, onSort }: TableHeadProps) {
  return (
    <th
      className={clsx(
        'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
        sortable && 'cursor-pointer hover:text-gray-700',
        className
      )}
      onClick={sortable ? onSort : undefined}
    >
      <div className="flex items-center gap-2">
        {children}
        {sortable && (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
        )}
      </div>
    </th>
  );
}

export function TableCell({ children, className }: BaseTableProps) {
  return (
    <td className={clsx('px-6 py-4 whitespace-nowrap text-sm text-gray-900', className)}>
      {children}
    </td>
  );
}
