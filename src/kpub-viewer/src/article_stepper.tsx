import { useState } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Stepper from '@mui/material/Stepper';
import StepContent from '@mui/material/StepContent';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import Typography from '@mui/material/Typography';
import { type BulkAssignerProps, AffiliationButtonGroup } from './bulk_assigner';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import { useStateContext, type Article } from './App';
import { apiURL, INSTRUMENTS } from './config';
import Highlighter from 'react-highlight-words';
import { ads_link } from './article_table';

interface ArticleStepperProps extends BulkAssignerProps { }

export const ArticleStepper = (props: ArticleStepperProps) => {
    const { selectedArticles, isOpen, handleClose, isKOA } = props;
    const [selectedOption, setSelectedOption] = useState('Keck');
    const [activeStep, setActiveStep] = useState(0);
    const context = useStateContext()

    const handleSave = async () => {
        // Perform the save operation here
        console.log('Selected Option:', selectedOption);
        console.log('activeStep:', activeStep)
        console.log('Article to be updated:', selectedArticles[activeStep]);

        const resp = await fetch(`${apiURL}/update_affiliation`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                [isKOA ? 'koa_affiliation' : 'affiliation']: selectedOption,
                articles: [selectedArticles[activeStep]],
            }),
        })

        if (resp.ok) {
            const respBody = await resp.json()
            console.log('Updated article:', respBody)
            if (context !== null) {
                var newArticles = [...context.articles]
                respBody.updated_articles.forEach((article: Article) => {
                    const idx = context?.articles.findIndex((a) => a._id === article._id)
                    if (idx > -1) {
                        newArticles.splice(idx, 1, article)
                    }
                })
                context?.setArticles(newArticles)
            }
        }
    }

    

    const handleNext = () => {
        //TODO: update the selected articles with the selected option
        setActiveStep((prevActiveStep) => prevActiveStep + 1);
        handleSave()
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
                    <>
                        {article.title.at(0)}
                        <a href={ads_link(article.bibcode)} target="_blank" rel="noopener noreferrer">{article.bibcode}</a>
                    </>
                </StepLabel>
                <StepContent>
                    <Box sx={{ mb: 2 }}>
                        <Stack>
                            {Object.entries(article.snippits ?? []).map((keysnip, idx) => {
                                const [key, value] = keysnip;
                                return (
                                    <Stack>
                                        <Typography key={idx} variant="body2">
                                            {key}: Mentioned {value.count} times
                                        </Typography>
                                        {value.snippets.map((snippet) => {
                                            return (
                                                <Highlighter
                                                    highlightClassName="highlighted"
                                                    searchWords={INSTRUMENTS}
                                                    autoEscape={true}
                                                    textToHighlight={snippet}
                                                />
                                            )
                                        })}
                                    </Stack>
                                )
                            }
                            )}
                            <>
                                <AffiliationButtonGroup
                                    selectedOption={selectedOption}
                                    setSelectedOption={setSelectedOption}
                                    row={true}
                                    isKOA={isKOA}
                                />
                                {/* <Select
                                    value={selectedOption}
                                    onChange={(e) => setSelectedOption(e.target.value)}
                                    fullWidth
                                >
                                    <MenuItem value="Keck">Keck</MenuItem>
                                    <MenuItem value="unknown">Unknown</MenuItem>
                                    <MenuItem value="unrelated">Unrelated</MenuItem>
                                </Select> */}
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

    const stepper_title = 'Stepper for verifiying ' + (isKOA ? 'KOA' : 'Keck') + ' article affiliation' 

    return (
        <Dialog maxWidth={'xl'} fullWidth open={isOpen} onClose={handleClose}>
            <DialogTitle>{stepper_title}</DialogTitle>
            <DialogContent>
                <Stepper activeStep={activeStep} orientation="vertical">
                    {step_components}
                </Stepper>
            </DialogContent>
            <DialogActions>
                <Stack justifyContent={'space-around'} direction="row" spacing={1}>
                    {activeStep >= selectedArticles.length && (
                        <>
                            <Typography variant="body2">
                                All articles have been updated with the selected {isKOA ? 'KOA' : 'Keck'}affiliation. You may exit.
                            </Typography>
                            <Button
                                onClick={handleBack}
                            >
                                Go Back
                            </Button>
                        </>
                    )}
                    <Button onClick={handleClose} color="secondary">
                        Close
                    </Button>
                </Stack>
            </DialogActions>
        </Dialog>
    )
}
