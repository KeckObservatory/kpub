import { DataGrid, type GridColDef, type GridComparatorFn, type GridRowSelectionModel, type GridToolbarProps, type ToolbarPropsOverrides } from '@mui/x-data-grid';
import { type Article } from './App';
import { ADS_URL } from './config'
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import { Toolbar } from '@mui/x-data-grid';
import { useEffect, useMemo, useState, type JSXElementConstructor, type ReactElement} from 'react';
import { BulkAssignerContent } from './bulk_assigner';
import { ArticleStepperContent } from './article_stepper';
import { MonthYearPicker } from './monthyear_picker';
import Tooltip from '@mui/material/Tooltip';
import DownloadIcon from '@mui/icons-material/Download';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
interface EditToolbarProps extends GridToolbarProps, ToolbarPropsOverrides {
    selectedArticles: Article[];
    isAdmin: boolean | null;
    allArticles: Article[];
}

export const ads_link = (x: string) => `${ADS_URL}/abs/${x}/abstract`

// Blank/undefined dates are treated as missing and always sorted below valid
// dates, in both ascending and descending order. MUI negates the comparator's
// result for descending sort, so we have to counter-negate the "missing value"
// branch based on the column's current sort direction (looked up via the api
// on the cell params) to keep missing values pinned to the bottom either way.
const dateSortComparator: GridComparatorFn<string | null | undefined> = (v1, v2, cellParams1) => {
    const t1 = v1 ? new Date(v1).getTime() : NaN;
    const t2 = v2 ? new Date(v2).getTime() : NaN;
    const invalid1 = Number.isNaN(t1);
    const invalid2 = Number.isNaN(t2);
    if (invalid1 && invalid2) return 0;
    if (invalid1 || invalid2) {
        const sortItem = cellParams1.api.getSortModel().find((item: { field: string }) => item.field === cellParams1.field);
        const isDesc = sortItem?.sort === 'desc';
        const raw = invalid1 ? 1 : -1;
        return isDesc ? -raw : raw;
    }
    return t1 - t2;
};

export const columns: GridColDef<Article>[] = [
    { field: 'title', headerName: 'TITLE', minWidth: 300, width: 837 },
    {
        field: 'bibcode', headerName: 'BIBCODE', width: 180,
        renderCell: (params) => {
            return (<a href={ads_link(params.value)} target="_blank" rel="noopener noreferrer">{params.value}</a>)

        }
    },
    { field: 'year', headerName: 'YEAR', width: 70 },
    { field: 'month', headerName: 'MONTH', width: 70 },
    { field: 'instruments', headerName: 'INST', width: 160 },
]

export const adminColumns = [
    ...columns,
    { field: 'archive', headerName: 'KOA?', width: 70 },
    { field: 'affiliation', headerName: 'AFFILIATION', width: 150 },
    { field: 'reason', headerName: 'REASON', width: 150 },
    { field: 'note', headerName: 'NOTE', width: 150 },
    { field: 'ilabel', headerName: 'ILABEL', width: 150 },
    { field: 'keck_score', headerName: 'KECK_SCORE', width: 100, valueFormatter: (value: number) => value != null ? value.toFixed(3) : '' },
    { field: 'idrp', headerName: 'iDRP', width: 100 },
    {
        field: 'drp_reason', headerName: 'DRP_REASON', width: 200,
        renderCell: (params: { value: ReactElement<unknown, string | JSXElementConstructor<any>>}) => (
            <Tooltip
                title={params.value ?? ''}
                placement="bottom-start"
                slotProps={{ tooltip: { sx: { fontSize: '0.95rem' } } }}
            >
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{params.value}</span>
            </Tooltip>
        )
    },
    { field: 'ikoa', headerName: 'iKOA', width: 100 },
    {
        field: 'koa_reason', headerName: 'KOA_REASON', width: 200,
        renderCell: (params: { value: ReactElement<unknown, string | JSXElementConstructor<any>>}) => (
            <Tooltip
                title={params.value ?? ''}
                placement="bottom-start"
                slotProps={{ tooltip: { sx: { fontSize: '0.95rem' } } }}
            >
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{params.value}</span>
            </Tooltip>
        )
    },
    {
        field: 'date_created', headerName: 'DATE_CREATED', width: 150,
        sortComparator: dateSortComparator,
    },
    {
        field: 'date_modified', headerName: 'DATE_MODIFIED', width: 150,
        sortComparator: dateSortComparator,
    },
    { field: 'last_modifier', headerName: 'LAST_MODIFIER', width: 150 },
    { field: 'has_acknowledgement', headerName: 'Acknowledgement?', width: 70 }
]

const exportArticlesToCsv = (articles: Article[], columnFields: string[], filename: string = 'articles.csv') => {
    if (articles.length === 0) return;

    // Create CSV header
    const headers = columnFields.join(',');

    // Create CSV rows
    const rows = articles.map(article => {
        return columnFields.map(field => {
            const value = (article as any)[field];
            // Handle null/undefined
            if (value === null || value === undefined) return '';
            // Quote fields that contain commas or quotes
            const strValue = String(value);
            if (strValue.includes(',') || strValue.includes('"') || strValue.includes('\n')) {
                return `"${strValue.replace(/"/g, '""')}"`;
            }
            return strValue;
        }).join(',');
    });

    // Combine header and rows
    const csv = [headers, ...rows].join('\n');

    // Create Blob and download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
};

interface AffiliationDialogProps {
    type: 'keckbulk' | 'keckstepper' | 'koabulk' | 'koastepper' | null;
    selectedArticles: Article[];
    isOpen: boolean;
    handleClose: () => void;
}

const AffiliationDialog = ({ type, selectedArticles, isOpen, handleClose }: AffiliationDialogProps) => {
    const isKOA = type?.startsWith('koa') ?? false;
    const isStepper = type?.endsWith('stepper') ?? false;

    const getTitle = () => {
        if (isStepper) {
            return `Stepper for verifying ${isKOA ? 'KOA' : 'Keck'} article affiliation`;
        }
        return 'Bulk Edit Selected Articles';
    };

    const maxWidth = isStepper ? 'xl' : 'sm';

    return (
        <Dialog maxWidth={maxWidth} fullWidth open={isOpen} onClose={handleClose}>
            <DialogTitle>{getTitle()}</DialogTitle>
            {isStepper ? (
                <ArticleStepperContent
                    selectedArticles={selectedArticles}
                    isKOA={isKOA}
                    handleClose={handleClose}
                />
            ) : (
                <BulkAssignerContent
                    selectedArticles={selectedArticles}
                    isKOA={isKOA}
                    handleClose={handleClose}
                />
            )}
        </Dialog>
    );
};



export function EditToolbar(props: EditToolbarProps) {
    const [menuOpen, setMenuOpen] = useState<null | HTMLElement>(null);
    const [activeDialog, setActiveDialog] = useState<'keckbulk' | 'keckstepper' | 'koabulk' | 'koastepper' | null>(null);

    const handleMenuClick = (event: React.MouseEvent<HTMLButtonElement>) => {
        setMenuOpen(event.currentTarget);
    }

    const handleMenuClose = () => {
        setMenuOpen(null);
    }

    const handleOpenDialog = (dialogType: 'keckbulk' | 'keckstepper' | 'koabulk' | 'koastepper') => {
        setActiveDialog(dialogType);
        handleMenuClose();
    };

    const handleCloseDialog = () => {
        setActiveDialog(null);
    };


    return (
        <Toolbar style={{ padding: '5px', marginTop: '20px', marginBottom: '20px' }}>
            <Stack sx={{ marginBottom: '20px' }} direction="row" spacing={5}>
                <MonthYearPicker />
                {props.isAdmin && (
                    <>
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                            <Button color="primary" onClick={handleMenuClick} variant="contained">
                                Admin Actions
                            </Button>
                            <Menu
                                anchorEl={menuOpen}
                                open={Boolean(menuOpen)}
                                onClose={handleMenuClose}
                            >
                                <MenuItem onClick={() => handleOpenDialog('keckstepper')}>
                                    Change Keck Affiliation of Selected Articles
                                </MenuItem>
                                <MenuItem onClick={() => handleOpenDialog('keckbulk')}>
                                    Bulk Change Keck Affiliation of Selected Articles
                                </MenuItem>
                                <MenuItem onClick={() => handleOpenDialog('koastepper')}>
                                    Change KOA Affiliation of Selected Articles
                                </MenuItem>
                                <MenuItem onClick={() => handleOpenDialog('koabulk')}>
                                    Bulk Change KOA Affiliation of Selected Articles
                                </MenuItem>
                            </Menu>
                        </div>

                        <AffiliationDialog
                            type={activeDialog}
                            selectedArticles={props.selectedArticles}
                            isOpen={activeDialog !== null}
                            handleClose={handleCloseDialog}
                        />
                    </>
                )}
                <Tooltip title={props.selectedArticles.length > 0 ? "Download selected articles as CSV" : "Download all articles as CSV"}>
                    <Button
                        size="small"
                        startIcon={<DownloadIcon />}
                        onClick={() => {
                            const articlesToExport = props.selectedArticles.length > 0 ? props.selectedArticles : props.allArticles;
                            const columnFields = props.isAdmin
                                ? (articlesToExport.length > 0 ? Object.keys(articlesToExport[0]) : [])
                                : columns.map(col => col.field);
                            exportArticlesToCsv(articlesToExport, columnFields, 'keck-articles.csv');
                        }}
                    >
                        Export {props.selectedArticles.length > 0 ? 'Selected' : 'All'}
                    </Button>
                </Tooltip>
            </Stack>
        </Toolbar>
    );
}

interface Props {
    articles: Article[];
    isAdmin: boolean | null;
}

export const ArticleTable = (props: Props) => {
    const { articles, isAdmin } = props;
    const [rowSelectionModel, setRowSelectionModel] = useState<GridRowSelectionModel>();

    const selectedArticles = useMemo(() => {
        // Get the selected rows based on the rowSelectionModel
        const sa = (articles ?? []).filter((row) =>
            rowSelectionModel?.ids.has(row._id)
        );
        // Perform an action with the selected rows (e.g., log them)
        console.log('Selected Articles:', sa);
        return sa ?? [];
    }, [rowSelectionModel]);

    useEffect(() => {
        // Log the articles whenever they change
        console.log('Articles updated:', articles);
        // Reset the row selection model when articles change
    }, [articles]);
    let cols = isAdmin ? adminColumns : columns as GridColDef<Article>[]
    if (isAdmin) {
        console.log('Setting title column minWidth');
        cols.map((col) => {
            if (col.field === 'title') {
                col.width = 300;
                return col;
            }
            else if (col.field === 'instruments') {
                col.width = 200;
                return col;
            }
            else if (col.field === 'has_acknowledgement') {
                col.width = 200;
                return col;
            }
            return col;
        })
    }

    return (
        <DataGrid
            getRowId={(row: Article) => row._id}
            getRowHeight={() => 'auto'}
            slots={{
                //@ts-ignore
                toolbar: EditToolbar // Custom toolbar component
            }
            }
            slotProps={{
                toolbar: {
                    selectedArticles: selectedArticles,
                    isAdmin: isAdmin,
                    allArticles: articles ?? []
                } as EditToolbarProps,
            }}
            showToolbar
            onRowSelectionModelChange={(newRowSelectionModel: any) => {
                console.log('newRowSelectionModel', newRowSelectionModel);
                setRowSelectionModel(newRowSelectionModel);
            }}
            rowSelectionModel={rowSelectionModel}
            checkboxSelection={true}
            disableMultipleRowSelection={false}
            rows={articles ?? []}
            columns={cols as GridColDef<Article>[]}
        />
    );
};

