import { useState, useEffect } from 'react';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Stepper from '@mui/material/Stepper';
import StepContent from '@mui/material/StepContent';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import Typography from '@mui/material/Typography';
import { AffiliationButtonGroup } from './bulk_assigner';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import { useStateContext, type Article } from './App';
import { apiURL, INSTRUMENTS } from './config';
import Highlighter from 'react-highlight-words';
import { ads_link } from './article_table';

interface ArticleStepperContentProps {
    selectedArticles: Article[];
    isKOA: boolean;
    handleClose: () => void;
}

export const ArticleStepperContent = (props: ArticleStepperContentProps) => {
    const { selectedArticles, isKOA, handleClose } = props;
    const [selectedOption, setSelectedOption] = useState('Keck');
    const [note, setNote] = useState('');
    const [instruments, setInstruments] = useState<string[]>([]);
    const [activeStep, setActiveStep] = useState(0);
    const context = useStateContext()

    const currentArticle = selectedArticles[activeStep];

    useEffect(() => {
        setInstruments((currentArticle?.instruments ?? []).filter((inst) => INSTRUMENTS.includes(inst)));
    }, [activeStep]);

    const handleSave = async () => {
        console.log('Selected Option:', selectedOption);
        console.log('activeStep:', activeStep)
        console.log('Article to be updated:', selectedArticles[activeStep]);

        const body: any = {
            [isKOA ? 'koa_affiliation' : 'affiliation']: selectedOption,
            articles: [selectedArticles[activeStep]],
        };

        if (note.trim()) {
            body.note = note;
        }

        // always send somthing in body.instruments to trigger backend update, even if it's an empty array after filtering out invalid instruments
        body.instruments = instruments ? instruments.filter((inst) => INSTRUMENTS.includes(inst)) : [];

        const resp = await fetch(`${apiURL}/update_affiliation`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
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

    const handleNextWithSave = () => {
        setActiveStep((prevActiveStep) => prevActiveStep + 1);
        setNote('');
        handleSave()
    };

    const handleNextWithoutSave = () => {
        setActiveStep((prevActiveStep) => prevActiveStep + 1);
        setNote('');
    };

    const handleBack = () => {
        setActiveStep((prevActiveStep) => prevActiveStep - 1);
        setNote('');
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
                                <TextField
                                    label="Note"
                                    multiline
                                    rows={3}
                                    fullWidth
                                    value={note}
                                    onChange={(e) => setNote(e.target.value)}
                                    placeholder="Enter any notes about this article"
                                    sx={{ mt: 2, mb: 2 }}
                                />
                                <FormControl fullWidth sx={{ mb: 2 }}>
                                    <FormLabel>Instruments</FormLabel>
                                    <Typography variant="caption" sx={{ mb: 1, color: 'text.secondary' }}>
                                        Current: {currentArticle?.instruments?.join(', ') || 'None'}
                                    </Typography>
                                    <FormGroup>
                                        <FormControlLabel
                                            control={
                                                <Checkbox
                                                    checked={instruments.length === INSTRUMENTS.length}
                                                    onChange={(e) => {
                                                        if (e.target.checked) {
                                                            setInstruments(INSTRUMENTS);
                                                        } else {
                                                            setInstruments([]);
                                                        }
                                                    }}
                                                />
                                            }
                                            label="Select All"
                                        />
                                    </FormGroup>
                                    <FormGroup row>
                                        {INSTRUMENTS.map((instrument) => (
                                            <FormControlLabel
                                                key={instrument}
                                                control={
                                                    <Checkbox
                                                        checked={instruments.includes(instrument)}
                                                        onChange={(e) => {
                                                            if (e.target.checked) {
                                                                setInstruments([...instruments, instrument].filter((inst) => INSTRUMENTS.includes(inst)));
                                                            } else {
                                                                setInstruments(
                                                                    instruments.filter((inst) => inst !== instrument).filter((inst) => INSTRUMENTS.includes(inst))
                                                                );
                                                            }
                                                        }}
                                                    />
                                                }
                                                label={instrument}
                                            />
                                        ))}
                                    </FormGroup>
                                </FormControl>
                                <Button
                                    disabled={selectedOption ? false : true}
                                    variant="contained"
                                    onClick={handleNextWithSave}
                                    sx={{ mt: 1, mr: 1 }}
                                >
                                    {index === selectedArticles.length - 1 ? 'Finish & Save' : 'Continue & Save'}
                                </Button>
                                <Button
                                    disabled={selectedOption ? false : true}
                                    variant="outlined"
                                    onClick={handleNextWithoutSave}
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
        <>
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
        </>
    )
}