import { DataGrid, type GridColDef, type GridRowSelectionModel, type GridToolbarProps, type ToolbarPropsOverrides } from '@mui/x-data-grid';
import Box from '@mui/material/Box';
import { type Article } from './App';
import { rows, columns } from './config'
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import { Toolbar, ToolbarButton } from '@mui/x-data-grid';
import { useEffect, useMemo, useState } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Stepper from '@mui/material/Stepper';
import StepContent from '@mui/material/StepContent';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import Typography from '@mui/material/Typography';


interface EditToolbarProps extends GridToolbarProps, ToolbarPropsOverrides {
    selectedArticles: Article[];
}

interface BulkEditDialogProps {
    selectedArticles: Article[];
    isOpen: boolean;
    handleClose: () => void;
}

interface EditStepperProps extends BulkEditDialogProps { }

function EditDialogStepper(props: EditStepperProps) {
    const { selectedArticles, isOpen, handleClose} = props;
    const [selectedOption, setSelectedOption] = useState('Keck');
    const [activeStep, setActiveStep] = useState(0);

    const handleSave = () => {
        // Perform the save operation here
        console.log('Selected Option:', selectedOption);
        console.log('Selected Articles:', selectedArticles);
    }

    const handleNext = () => {
        //TODO: update the selected articles with the selected option
        setActiveStep((prevActiveStep) => prevActiveStep + 1);
    };

    const handleBack = () => {
        setActiveStep((prevActiveStep) => prevActiveStep - 1);
    };

    const step_components = selectedArticles.map((article, index) => {
        return (
            <Step key={article._id}>
                <StepLabel
                    optional={
                        index === selectedArticles.length - 1 ? (
                            <Typography variant="caption">Last step</Typography>
                        ) : null
                    }
                >
                    {article.title.at(0)}
                </StepLabel>
                <StepContent>
                    <Box sx={{ mb: 2 }}>
                        <Stack>
                            {Object.entries(article.snippits).map((keysnip, idx) => {
                                const [key, value] = keysnip;
                                return (
                                    <Stack>
                                        <Typography key={idx} variant="body2">
                                            {key}: {value.count}
                                        </Typography>
                                        {value.snippets.map((snippet, jdx) => {
                                            return (<Typography key={jdx} variant="body2">
                                                {jdx + 1}: {snippet}
                                            </Typography>)
                                        })}
                                    </Stack>
                                )
                            }
                            )}
                            <>
                                <Select
                                    value={selectedOption}
                                    onChange={(e) => setSelectedOption(e.target.value)}
                                    fullWidth
                                >
                                    <MenuItem value="Keck">Keck</MenuItem>
                                    <MenuItem value="unknown">Unknown</MenuItem>
                                    <MenuItem value="unrelated">Unrelated</MenuItem>
                                </Select>
                                <Button
                                    disabled={selectedOption ? false : true}
                                    variant="contained"
                                    onClick={handleNext}
                                    sx={{ mt: 1, mr: 1 }}
                                >
                                    {index === selectedArticles.length - 1 ? 'Finish' : 'Continue'}
                                </Button>
                                <Button
                                    disabled={index === 0}
                                    onClick={handleBack}
                                    sx={{ mt: 1, mr: 1 }}
                                >
                                    Back
                                </Button>
                            </>
                        </Stack>
                    </Box>
                </StepContent>
            </Step>
        )
    })

    return (
        <Dialog maxWidth={'xl'} open={isOpen} onClose={handleClose}>
            <DialogTitle>Stepper for verifiying article affiliation</DialogTitle>
            <DialogContent>
            <Stepper activeStep={activeStep} orientation="vertical">
                {step_components}
            </Stepper>
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} color="secondary">
                    Cancel
                </Button>
            </DialogActions>
        </Dialog>
    )
}

function BulkEditDialog(props: BulkEditDialogProps) {

    const { selectedArticles, isOpen, handleClose} = props;

    const [selectedOption, setSelectedOption] = useState('Keck');


    const handleSave = () => {
        // Perform the save operation here
        console.log('Selected Option:', selectedOption);
        console.log('Selected Articles:', selectedArticles);
        //TODO: update the selected articles with the selected option
        // Close the dialog
        handleClose();
        // refresh the table with the updated data
    };

    return (
        <Dialog open={isOpen} onClose={handleClose}>
            <DialogTitle>Bulk Edit Selected Articles</DialogTitle>
            <DialogContent>
                <Select
                    value={selectedOption}
                    onChange={(e) => setSelectedOption(e.target.value)}
                    fullWidth
                >
                    <MenuItem value="Keck">Keck</MenuItem>
                    <MenuItem value="unknown">Unknown</MenuItem>
                    <MenuItem value="unrelated">Unrelated</MenuItem>
                </Select>
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} color="secondary">
                    Cancel
                </Button>
                <Button onClick={handleSave} color="primary" variant="contained">
                    Save
                </Button>
            </DialogActions>
        </Dialog>
    )
}


export function EditToolbar(props: EditToolbarProps) {
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [isStepperOpen, setIsStepperOpen] = useState(false);

    const openDialog = (type: string) => {
        if (type === 'bulk') {
            handleOpenDialog()
        } else if (type === 'stepper') {
            handleOpenStepper()
        }
    }

    const handleOpenDialog = () => {
        setIsDialogOpen(true);
        setIsStepperOpen(false);
    };

    const handleCloseDialog = () => {
        setIsDialogOpen(false);
    };

    const handleOpenStepper = () => {
        setIsStepperOpen(true);
        setIsDialogOpen(false);
    };

    const handleCloseStepper = () => {
        setIsStepperOpen(false);
    };

    return (
        // <GridToolbarContainer sx={{ justifyContent: 'center' }}>
        <Toolbar >
            <Stack justifyContent={'space-evenly'} direction="row" spacing={1}>
                <Button color="primary" onClick={() => openDialog('bulk')} variant="contained">
                    Change Affiliation of Selected Articles
                </Button>
                <Button color="primary" onClick={() => openDialog('stepper')} variant="contained">
                    Bulk Change Affiliation of Selected Articles
                </Button>
            </Stack>
            <EditDialogStepper
                selectedArticles={props.selectedArticles}
                isOpen={isDialogOpen}
                handleClose={handleCloseDialog}
            />
            <BulkEditDialog
                selectedArticles={props.selectedArticles}
                isOpen={isStepperOpen}
                handleClose={handleCloseStepper}
            />
        </Toolbar>
    );
}

export const ArticleTable = () => {
    const [rowSelectionModel, setRowSelectionModel] = useState<GridRowSelectionModel>();
    const selectedArticles = useMemo(() => {
        // Get the selected rows based on the rowSelectionModel
        const sa = (rows as unknown as Article[]).filter((row) =>
            rowSelectionModel?.ids.has(row._id)
        );

        // Perform an action with the selected rows (e.g., log them)
        console.log('Selected Articles:', sa);
        return sa;
    }, [rowSelectionModel]);

    return (
        <Box
            sx={{
                height: 1000,
                width: '100%',
            }}
        >
            <DataGrid
                getRowId={(row) => row._id}
                getRowHeight={() => 'auto'}
                slots={{
                    //@ts-ignore
                    toolbar: EditToolbar // Custom toolbar component
                }
                }
                slotProps={{
                    toolbar: {
                        selectedArticles: selectedArticles
                    } as EditToolbarProps,
                }}
                showToolbar
                onRowSelectionModelChange={(newRowSelectionModel) => {
                    console.log('newRowSelectionModel', newRowSelectionModel);
                    setRowSelectionModel(newRowSelectionModel);
                }}
                rowSelectionModel={rowSelectionModel}
                checkboxSelection={true}
                disableMultipleRowSelection={false}
                rows={rows as any as Article[]}
                columns={columns as GridColDef<Article>[]}
            />
        </Box>
    );
};