import { DataGrid, type GridColDef, type GridRowSelectionModel, type GridToolbarProps, type ToolbarPropsOverrides } from '@mui/x-data-grid';
import { type Article } from './App';
import { ADS_URL } from './config'
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import { Toolbar } from '@mui/x-data-grid';
import { useEffect, useMemo, useState } from 'react';
import { ArticleStepper } from './article_stepper';
import { BulkAssigner } from './bulk_assigner';
import { MonthYearPicker } from './monthyear_picker';
import Tooltip from '@mui/material/Tooltip';
import DownloadIcon from '@mui/icons-material/Download';

interface EditToolbarProps extends GridToolbarProps, ToolbarPropsOverrides {
    selectedArticles: Article[];
    isAdmin: boolean | null;
    allArticles: Article[];
}

export const ads_link = (x: string) => `${ADS_URL}/abs/${x}/abstract`

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
    { field: 'ilabel', headerName: 'ILABEL', width: 150 },
    { field: 'keck_score', headerName: 'KECK_SCORE', width: 100, valueFormatter: (value: number) => value != null ? value.toFixed(3) : '' },
    { field: 'date_modified', headerName: 'DATE_MODIFIED', width: 150 },
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



export function EditToolbar(props: EditToolbarProps) {
    const [isKOADialogOpen, setIsKOADialogOpen] = useState(false);
    const [isKOAStepperOpen, setIsKOAStepperOpen] = useState(false);
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [isStepperOpen, setIsStepperOpen] = useState(false);
    const [_, setIsPlotOpen] = useState(false);

    const openDialog = (type: string) => {
        if (type === 'bulk') {
            handleOpenDialog()
        } else if (type === 'stepper') {
            handleOpenStepper()
        }
        else if (type === 'plot') {
            handleOpenPlot()
        }
    }

    const openKOADialog = (type: string) => {
        if (type === 'bulk') {
            handleOpenKOADialog()
        } else if (type === 'stepper') {
            handleOpenKOAStepper()
        }
    }


    const handleOpenPlot = () => {
        setIsDialogOpen(false);
        setIsStepperOpen(false);
        setIsKOADialogOpen(false);
        setIsKOAStepperOpen(false);
        setIsPlotOpen(true);
    };

    const handleOpenDialog = () => {
        setIsDialogOpen(true);
        setIsStepperOpen(false);
        setIsKOADialogOpen(false);
        setIsKOAStepperOpen(false);
        setIsPlotOpen(false);
    };

    const handleCloseDialog = () => {
        setIsDialogOpen(false);
    };

    const handleOpenStepper = () => {
        setIsStepperOpen(true);
        setIsDialogOpen(false);
        setIsKOADialogOpen(false);
        setIsKOAStepperOpen(false);
        setIsPlotOpen(false);
    };

    const handleCloseStepper = () => {
        setIsStepperOpen(false);
    };

    const handleOpenKOADialog = () => {
        setIsDialogOpen(false);
        setIsStepperOpen(false);
        setIsKOADialogOpen(true);
        setIsKOAStepperOpen(false);
        setIsPlotOpen(false);
    };

    const handleCloseKOADialog = () => {
        setIsKOADialogOpen(false);
    };

    const handleOpenKOAStepper = () => {
        setIsStepperOpen(false);
        setIsDialogOpen(false);
        setIsKOADialogOpen(false);
        setIsKOAStepperOpen(true);
        setIsPlotOpen(false);
    };

    const handleCloseKOAStepper = () => {
        setIsKOAStepperOpen(false);
    };


    return (
        <Toolbar style={{ padding: '5px', marginTop: '20px', marginBottom: '20px' }}>
            <Stack sx={{ marginBottom: '20px' }} direction="row" spacing={5}>
                <MonthYearPicker />
                {props.isAdmin && (
                    <Stack direction="column" spacing={2}>
                        <Stack direction="row" spacing={2}>
                            <Button color="primary" onClick={() => openDialog('bulk')} variant="contained">
                                Change Keck Affiliation of Selected Articles
                            </Button>
                            <Button color="primary" onClick={() => openDialog('stepper')} variant="contained">
                                Bulk Change Keck Affiliation of Selected Articles
                            </Button>
                            <ArticleStepper
                                selectedArticles={props.selectedArticles}
                                isOpen={isDialogOpen}
                                handleClose={handleCloseDialog}
                                isKOA={false}
                            />
                            <BulkAssigner
                                selectedArticles={props.selectedArticles}
                                isOpen={isStepperOpen}
                                handleClose={handleCloseStepper}
                                isKOA={false}
                            />
                            <Stack direction="row" spacing={2}>
                                <Button color="primary" onClick={() => openKOADialog('bulk')} variant="contained">
                                    Change KOA Affiliation of Selected Articles
                                </Button>
                                <Button color="primary" onClick={() => openKOADialog('stepper')} variant="contained">
                                    Bulk Change KOA Affiliation of Selected Articles
                                </Button>
                                <ArticleStepper
                                    selectedArticles={props.selectedArticles}
                                    isOpen={isKOADialogOpen}
                                    handleClose={handleCloseKOADialog}
                                    isKOA={true}
                                />
                                <BulkAssigner
                                    selectedArticles={props.selectedArticles}
                                    isOpen={isKOAStepperOpen}
                                    handleClose={handleCloseKOAStepper}
                                    isKOA={true}
                                />
                            </Stack>
                        </Stack>
                    </Stack>
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
            columns={cols}
        />
    );
};

