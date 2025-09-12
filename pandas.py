import csv
import os

class errors:
    class EmptyDataError(Exception):
        pass

class Series(list):
    def tolist(self):
        return list(self)

class Columns(list):
    def tolist(self):
        return list(self)

class RowProxy:
    def __init__(self, data):
        self._data = data
    def __getitem__(self, key):
        return self._data.get(key)

class ILoc:
    def __init__(self, df):
        self._df = df
    def __getitem__(self, idx):
        if isinstance(idx, tuple) and len(idx) == 2:
            row_idx, col_idx = idx
            if not self._df._rows:
                raise IndexError("no rows")
            row = self._df._rows[row_idx]
            col_name = self._df.columns[col_idx]
            return row.get(col_name)
        else:
            row = self._df._rows[idx]
            return RowProxy(row)

class DataFrame:
    def __init__(self, data=None, columns=None):
        if isinstance(data, DataFrame):
            self.columns = Columns(list(data.columns))
            self._rows = [dict(r) for r in data._rows]
            return
        data = data or []
        self._rows = []
        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                # list of dicts
                self.columns = Columns(list(data[0].keys()))
                for d in data:
                    self._rows.append(dict(d))
            elif data and isinstance(data[0], (list, tuple)):
                self.columns = Columns(list(columns or []))
                for row in data:
                    self._rows.append({self.columns[i]: row[i] for i in range(len(self.columns))})
            else:
                self.columns = Columns(list(columns or []))
        else:
            self.columns = Columns(list(columns or []))
        self.iloc = ILoc(self)

    def to_csv(self, filename, index=False):
        # Write header if columns exist, else write empty file
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', newline='') as f:
            if self.columns:
                writer = csv.writer(f)
                writer.writerow(list(self.columns))
                for row in self._rows:
                    writer.writerow([row.get(col) for col in self.columns])
            else:
                # write nothing for empty DataFrame (0 bytes)
                f.write("")

    def __len__(self):
        return len(self._rows)

    @property
    def empty(self):
        return len(self) == 0

    def __getitem__(self, col_name):
        return Series([row.get(col_name) for row in self._rows])


def read_csv(filename):
    if os.path.getsize(filename) == 0:
        raise errors.EmptyDataError("No columns to parse from file")
    with open(filename, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
        if not rows:
            raise errors.EmptyDataError("No columns to parse from file")
        cols = rows[0]
        data = [dict(zip(cols, r)) for r in rows[1:]]
        return DataFrame(data)


def concat(dfs, ignore_index=False):
    if not dfs:
        return DataFrame([])
    # Assume all dataframes have the same columns
    cols = list(dfs[0].columns)
    combined_rows = []
    for df in dfs:
        combined_rows.extend(df._rows)
    return DataFrame(combined_rows, columns=cols)
