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


interface EditToolbarProps extends GridToolbarProps, ToolbarPropsOverrides {
    selectedArticles: Article[];
    isAdmin: boolean | null;
}

export const ads_link = (x:string) => `${ADS_URL}/abs/${x}/abstract`

export const columns: GridColDef<Article>[]  = [
    { field: 'title', headerName: 'TITLE', width: 300 },
    { field: 'bibcode', headerName: 'BIBCODE', width: 180, 
        renderCell: (params) => {
            return (<a href={ads_link(params.value)} target="_blank" rel="noopener noreferrer">{params.value}</a>)

    }},
    { field: 'year', headerName: 'YEAR', width: 70 },
    { field: 'month', headerName: 'MONTH', width: 70 },
    { field: 'instruments', headerName: 'INST', width: 90 },
]

export const adminColumns = [
    ...columns,
    { field: 'id', headerName: 'ID', width: 90 },
    { field: 'archive', headerName: 'KOA?', width: 70 },
    { field: 'affiliation', headerName: 'AFFILIATION', width: 150 },
    { field: 'date_modified', headerName: 'DATE_MODIFIED', width: 150 },
    { field: 'last_modifier', headerName: 'LAST_MODIFIER', width: 150 }
]



export function EditToolbar(props: EditToolbarProps) {
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


    const handleOpenPlot = () => {
        setIsDialogOpen(false);
        setIsStepperOpen(false);
        setIsPlotOpen(true);
    };

    const handleOpenDialog = () => {
        setIsDialogOpen(true);
        setIsStepperOpen(false);
        setIsPlotOpen(false);
    };

    const handleCloseDialog = () => {
        setIsDialogOpen(false);
    };

    const handleOpenStepper = () => {
        setIsStepperOpen(true);
        setIsDialogOpen(false);
        setIsPlotOpen(false);
    };

    const handleCloseStepper = () => {
        setIsStepperOpen(false);
    };

    return (
        <Toolbar style={{padding: '5px', marginTop: '20px', marginBottom: '20px' }}> 
            <Stack sx={{marginBottom: '20px'}}direction="row" spacing={5}>
                <MonthYearPicker />
                {props.isAdmin && (
                    <>
                        <Button color="primary" onClick={() => openDialog('bulk')} variant="contained">
                            Change Affiliation of Selected Articles
                        </Button>
                        <Button color="primary" onClick={() => openDialog('stepper')} variant="contained">
                            Bulk Change Affiliation of Selected Articles
                        </Button>
                        <ArticleStepper
                            selectedArticles={props.selectedArticles}
                            isOpen={isDialogOpen}
                            handleClose={handleCloseDialog}
                        />
                        <BulkAssigner
                            selectedArticles={props.selectedArticles}
                            isOpen={isStepperOpen}
                            handleClose={handleCloseStepper}
                        />
                    </>
                )}
            </Stack>
        </Toolbar>
    );
}

interface Props {
    articles: Article[];
    isAdmin: boolean | null;
}

export const ArticleTable = (props: Props ) => {
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
    const cols = isAdmin ? adminColumns : columns as GridColDef<Article>[]

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
                    isAdmin: isAdmin
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

