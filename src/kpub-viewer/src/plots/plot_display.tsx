import Plot from 'react-plotly.js';
import { apiURL } from '../config';
import { useEffect, useState, useMemo } from 'react'
import type { CountType, PlotNames } from './plot_control';

interface PlotDataByInstrument {
    years: number[],
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
    year_begin?: number,
    instruments?: string[],
    extrapolate?: boolean,
    countType?: CountType
}

export const PlotDisplay = (props: Props) => {

    const { plotname, year_begin, instruments, extrapolate, countType } = props
    const [traces, setTraces] = useState<any>([])
    const [layout, setLayout] = useState<any>({})

    if (!plotname) {
        return null
    }

    const plot_data = useMemo(async () => {
        switch (plotname) {
            case 'data_by_instrument':
                const iresp = await fetch(`${apiURL}/get_plot?plotname=plot_by_instrument&instruments=${instruments?.join('|') || ''}&extrapolate=${extrapolate || false}`)
                const idata = await iresp.json() as PlotDataByInstrument
                return idata
            case 'data_by_year':
                const yresp = await fetch(`${apiURL}/get_plot?plotname=plot_by_year&instruments=${instruments?.join('|') || ''}&extrapolate=${extrapolate || false}`)
                const ydata = await yresp.json() as PlotDataByYear
                return ydata
            case 'data_by_count':
                const cresp = await fetch(`${apiURL}/get_plot?plotname=plot_author_count&instruments=${instruments?.join('|') || ''}&extrapolate=${extrapolate || false}`)
                const cdata = await cresp.json() as PlotDataByCount
                return cdata
            default:
                const dresp = await fetch(`${apiURL}/get_plot?plotname=plot_by_instrument&instruments=${instruments?.join('|') || ''}&extrapolate=${extrapolate || false}`)
                const ddata = await dresp.json() as PlotDataByInstrument
                return ddata
        }
    }, [plotname, extrapolate])

    useEffect(() => {

        const fetchData = async () => {
            const dt = await plot_data
            if (!dt) {
                console.warn('No data returned for plot:', plotname)
                return
            }

            console.log('Plot data:', dt)
            let data: any 
            let newLayout: any = {}
            let newTraces: any = []
            switch (plotname) {
                case 'data_by_instrument':
                    data = dt as PlotDataByInstrument

                    let indexes: number[] = [];

                    (data as PlotDataByInstrument).columns.forEach((col: string, idx: number) => {
                        if (instruments?.includes(col)) {
                            indexes.push(idx);
                        }
                    });
                    const columns = (data as PlotDataByInstrument).columns.filter((_col: string, idx: number) => {
                        return indexes.includes(idx);
                    });
                    // Use all years, since years is a 1D array for all columns
                    const years = (data as PlotDataByInstrument).years;
                    // Filter values and colors by indexes
                    const values = (data as PlotDataByInstrument).values.filter((_col: number[], idx: number) => {
                        return indexes.includes(idx);
                    });
                    const colors = (data as PlotDataByInstrument).color.filter((_col: string, idx: number) => {
                        return indexes.includes(idx);
                    });
                    console.log('Data by instrument:', data)
                    newTraces = values.map((value: number[], index: number) => {
                        return {
                            x: years,
                            y: value,
                            name: columns[index],
                            marker: { color: colors[index] },
                            line: { width: 2, color: colors[index] },
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
                            range: [year_begin, data.years[data.years.length - 1]],
                            
                        },
                        yaxis: {
                            title: { text: 'Number of Papers' },
                        },
                        showlegend: true,
                        legend: {
                            orientation: 'h',
                            xanchor: 'center',
                            yanchor: 'right',
                            x: 0.5,
                            y: -0.3,
                        },
                    }
                    break;
                case 'data_by_year':
                    data = dt as unknown as PlotDataByYear
                    console.log('Data by year:', data)
                    const color = data.colors[0]
                    let x: number[] = []
                    let y: number[] = []
                    Object.entries(data.counts).forEach( ([year, count]: [string, unknown]) => {
                        x.push(Number(year))
                        y.push(count as number)
                    })
                    newTraces = [
                        {
                            x: x,
                            y: y,
                            type: 'bar',
                            name: 'Keck',
                            marker: { color },
                        }
                    ]
                    newLayout = {
                        title: { text: 'Data by Year' },
                        size: {
                            width: 800,
                            height: 600,
                        },
                        xaxis: {
                            title: { text: 'Year' },
                            tickvals: x,
                            range: [year_begin, x[x.length - 1]],
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
                            y: -0.3,
                        },
                    }
                    break;
                case 'data_by_count':
                    data = dt as unknown as PlotDataByCount
                    const key = `${countType}_counts`
                    console.log('Data by count:', data, key)
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
                            tickvals: data.cumulative_years,
                            range: [year_begin, data.cumulative_years[data.cumulative_years.length - 1]],
                        },
                        yaxis: {
                            title: { text: countType === 'first_author' ? 'First Author Count' : countType === 'author' ? 'Author Count' : 'Paper Count' },
                        },
                        showlegend: true,
                        legend: {
                            orientation: 'h',
                            xanchor: 'center',
                            yanchor: 'bottom',
                            x: 0.5,
                            y: -0.3,
                        },
                    }
                    break;
            }
            console.log('New traces:', newTraces)
            console.log('New layout:', newLayout)
            setTraces(newTraces)
            setLayout(newLayout)
        }
        fetchData()
    }, [plot_data, countType, instruments, year_begin, extrapolate])

    return (
        <Plot
            data={traces}
            layout={layout}
        />
    )
}