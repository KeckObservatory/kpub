import Plot from 'react-plotly.js';
//import { apiURL, mock_plot_by_count, mock_plot_data_by_instrument, mock_plot_data_by_year } from '../config';
import { apiURL } from '../config';
import { useEffect, useState, useMemo } from 'react'
import type { CountType, PlotNames } from './plot_control';

interface PlotDataByInstrument {
    years: string[],
    values: number[][],
    columns: string[],
    color: string[]
}

interface PlotDataByCount {
    cumulative_years: number[],
    paper_counts: number[],
    author_counts: number[],
    first_author_counts: number[]

}

interface PlotDataByYear {
    current_year: number,
    current_total?: number,
    expected?: number,
    year_begin: number,
    counts: { [key: number]: number },
    colors: string[]
}

interface Props {
    plotname: PlotNames,
    start_year?: number,
    instruments?: string[],
    extrapolate?: boolean,
    countType?: CountType
}

export const PlotDisplay = (props: Props) => {

    const { plotname, start_year, instruments, extrapolate, countType } = props
    const [traces, setTraces] = useState<any>([])
    const [layout, setLayout] = useState<any>({})

    if (!plotname) {
        return null
    }

    const plot_data = useMemo(async () => {
        switch (plotname) {
            case 'data_by_instrument':
                const iresp = await fetch(`${apiURL}/get_plot?plotname=plot_data_by_instrument&start_year=${start_year || 2000}&instruments=${instruments?.join('|') || ''}&extrapolate=${extrapolate || false}`)
                const idata = await iresp.json() as PlotDataByInstrument
                return idata 
            case 'data_by_year':
                const yresp = await fetch(`${apiURL}/get_plot?plotname=plot_data_by_year&start_year=${start_year || 2000}&instruments=${instruments?.join('|') || ''}&extrapolate=${extrapolate || false}`)
                const ydata = await yresp.json() as PlotDataByYear
                return ydata
            case 'data_by_count':
                const cresp = await fetch(`${apiURL}/get_plot?plotname=plot_data_by_count&start_year=${start_year || 2000}&instruments=${instruments?.join('|') || ''}&extrapolate=${extrapolate || false}&count_type=${countType || 'paper'}`)
                const cdata = await cresp.json() as PlotDataByCount
                return cdata
            default:
                const dresp = await fetch(`${apiURL}/get_plot?plotname=plot_data_by_instrument&start_year=${start_year || 2000}&instruments=${instruments?.join('|') || ''}&extrapolate=${extrapolate || false}`)
                const ddata = await dresp.json() as PlotDataByInstrument
                return ddata 
        }
    }, [plotname, start_year, instruments, extrapolate])

    useEffect(() => {
        console.log('Plot data:', plot_data)
        let data: any
        let newLayout: any = {}
        let newTraces: any = []
        switch (plotname) {
            case 'data_by_instrument':
                data = plot_data as unknown as PlotDataByInstrument
                newTraces = data.values.map((value: number, index: number) => {
                    return {
                        x: data.years,
                        y: value,
                        type: 'line+scatter',
                        name: data.columns[index],
                        marker: { color: data.color[index] },
                        line: { width: 2, shape: 'spline', color: data.color[index] },
                        mode: 'lines+markers',
                    }
                })
                newLayout = {
                    title: { text: 'Data by Instrument' },
                    size: {
                        width: 800,
                        height: 600,
                    },
                    xaxis: {
                        title: { text: 'Year' },
                        tickvals: data.years,
                    },
                    yaxis: {
                        title: { text: 'Number of Papers' },
                    },
                    showlegend: true,
                    // legend: {
                    //     orientation: 'h',
                    //     xanchor: 'center',
                    //     yanchor: 'bottom',
                    //     x: 0.5,
                    //     y: -0.2,
                    // },
                }
                break;
            case 'data_by_year':
                data = plot_data as unknown as PlotDataByYear
                newTraces = data.colors.map((color: string) => {
                    return {
                        x: Object.keys(data.counts.keck),
                        y: Object.values(data.counts.keck),
                        type: 'bar',
                        name: 'Keck',
                        marker: { color: color },
                    }
                })
                newLayout = {
                    title: { text: 'Data by Year' },
                    size: {
                        width: 800,
                        height: 600,
                    },
                    xaxis: {
                        title: { text: 'Year' },
                        tickvals: Object.keys(data.counts.keck),
                    },
                    yaxis: {
                        title: { text: 'Number of Papers' },
                    },
                    showlegend: true,
                    legend: {
                        orientation: 'h',
                        xanchor: 'center',
                        yanchor: 'bottom',
                        x: 0.5,
                        y: -0.2,
                    },
                }
                break;
            case 'data_by_count':
                data = plot_data as unknown as PlotDataByCount
                const key = `${countType}_counts`
                newTraces = [{
                    x: data.cumulative_years,
                    y: data[key],
                    type: 'line+scatter',
                    name: 'Paper Count',
                }]
                newLayout = {
                    title: { text: key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') },
                    xaxis: {
                        title: { text: 'Year' },
                    },
                    yaxis: {
                        title: { text: countType === 'first_author' ? 'First Author Count' : countType === 'author' ? 'Author Count' : 'Paper Count' },
                    },
                    showlegend: true,
                }
                break;
        }
        console.log('New traces:', newTraces)
        console.log('New layout:', newLayout)
        setTraces(newTraces)
        setLayout(newLayout)
    }, [plot_data, countType])

    return (
        <Plot
            data={traces}
            layout={layout}
        />
    )
}