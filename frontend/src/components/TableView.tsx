import { Table } from '@radix-ui/themes';

interface TableViewProps {
  data: string[][];
  columns: string[];
}

const TableView = ({ data, columns }: TableViewProps) => {
  return (
    <div className="w-full overflow-x-auto max-w-[100%]">
      <Table.Root variant="surface">
        <Table.Header>
          <Table.Row>
            {columns.map((column) => (
              <Table.ColumnHeaderCell key={column}>
                {column}
              </Table.ColumnHeaderCell>
            ))}
          </Table.Row>
        </Table.Header>

        <Table.Body>
          <Table.Row>
            {data.map((row) => (
              <Table.Row key={row.join(',')}>
                {row.map((cell) => (
                  <Table.Cell key={cell}>{cell}</Table.Cell>
                ))}
              </Table.Row>
            ))}
          </Table.Row>
        </Table.Body>
      </Table.Root>
    </div>
  );
};

export default TableView;
