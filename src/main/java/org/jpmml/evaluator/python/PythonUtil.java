/*
 * Copyright (c) 2021 Villu Ruusmann
 *
 * This file is part of JPMML-Evaluator
 *
 * JPMML-Evaluator is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * JPMML-Evaluator is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with JPMML-Evaluator.  If not, see <http://www.gnu.org/licenses/>.
 */
package org.jpmml.evaluator.python;

import java.io.IOException;
import java.util.AbstractMap;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import net.razorvine.pickle.Pickler;
import net.razorvine.pickle.Unpickler;
import net.razorvine.pickle.objects.ClassDict;
import numpy.core.Scalar;
import numpy.core.ScalarUtil;
import org.jpmml.evaluator.Evaluator;
import org.jpmml.evaluator.EvaluatorUtil;
import org.jpmml.python.PickleUtil;

public class PythonUtil {

	private PythonUtil(){
	}

	static
	public byte[] evaluateAll(Evaluator evaluator, byte[] dictBytes) throws IOException {
		Map<String, ?> argumentsDict = (Map)unpickle(dictBytes);

		Map<String, ?> resultsDict = evaluateAll(evaluator, argumentsDict);

		return pickle(resultsDict);
	}

	static
	public Map<String, ?> evaluateAll(Evaluator evaluator, Map<String, ?> argumentsDict){
		ColumnMapper argumentMapper = new ColumnMapper((List<String>)argumentsDict.get("columns"));
		List<List<?>> argumentData = (List<List<?>>)argumentsDict.get("data");

		ColumnMapper resultMapper = new ColumnMapper();
		List<List<?>> resultData = new ArrayList<>();

		TabularArguments arguments = new TabularArguments(argumentMapper);

		for(int i = 0; i < argumentData.size(); i++){
			List<?> argumentRow = argumentData.get(i);

			arguments.setRow(argumentRow);

			Map<String, ?> results = evaluator.evaluate(arguments);

			int numberOfColumns = resultMapper.size();

			List<Object> resultRow = new ArrayList<>(numberOfColumns);
			for(int j = 0; j < numberOfColumns; j++){
				resultRow.add(null);
			}

			Collection<? extends Map.Entry<String, ?>> entries = results.entrySet();
			for(Map.Entry<String, ?> entry : entries){
				String name = entry.getKey();
				Object value = EvaluatorUtil.decode(entry.getValue());

				Integer index = resultMapper.putIfAbsent(name, numberOfColumns);
				if(index == null){
					resultRow.add(value);

					numberOfColumns++;
				} else

				{
					resultRow.set(index, value);
				}
			}

			resultData.add(resultRow);
		}

		Map<String, Object> resultsDict = new HashMap<>();
		resultsDict.put("columns", new ArrayList<>(resultMapper.getColumns()));
		resultsDict.put("data", resultData);

		return resultsDict;
	}

	static
	public byte[] evaluate(Evaluator evaluator, byte[] dictBytes) throws IOException {
		Map<String, ?> arguments = (Map)unpickle(dictBytes);

		Map<String, ?> results = evaluate(evaluator, arguments);

		return pickle(results);
	}

	static
	public Map<String, ?> evaluate(Evaluator evaluator, Map<String, ?> arguments){
		Map<String, Object> pmmlArguments = new AbstractMap<String, Object>(){

			@Override
			public Object get(Object key){
				Object value = arguments.get(key);

				return toJavaPrimitive(value);
			}

			@Override
			public Set<Entry<String, Object>> entrySet(){
				throw new UnsupportedOperationException();
			}
		};

		Map<String, ?> pmmlResults = evaluator.evaluate(pmmlArguments);

		return EvaluatorUtil.decodeAll(pmmlResults);
	}

	static
	public byte[] argumentsToResults(byte[] dictBytes) throws IOException {
		Map<String, ?> arguments = (Map)unpickle(dictBytes);

		Map<String, Object> results = new LinkedHashMap<>();

		Collection<? extends Map.Entry<String, ?>> entries = arguments.entrySet();
		for(Map.Entry<String, ?> entry : entries){
			String key = entry.getKey();
			Object value = entry.getValue();

			results.put(key, toJavaPrimitive(value));
		}

		return pickle(results);
	}

	static
	public Object toJavaPrimitive(Object value){

		if(value == null){
			return value;
		} // End if

		if(value instanceof String){
			return value;
		} else

		if(value instanceof Boolean){
			return value;
		} else

		if(value instanceof Number){
			return value;
		} else

		if(value instanceof Scalar){
			Scalar scalar = (Scalar)value;

			return ScalarUtil.decode(scalar);
		} else

		if(value instanceof ClassDict){
			ClassDict classDict = (ClassDict)value;

			throw new IllegalArgumentException("Python type " + classDict.getClassName() + " is not supported");
		} else

		{
			throw new IllegalArgumentException("Java type " + (value.getClass()).getName() + " is not supported");
		}
	}

	static
	private Object unpickle(byte[] bytes) throws IOException {
		Unpickler unpickler = new Unpickler();

		return unpickler.loads(bytes);
	}

	static
	private byte[] pickle(Object object) throws IOException {
		Pickler pickler = new Pickler();

		return pickler.dumps(object);
	}

	static
	private class ColumnMapper extends HashMap<String, Integer> {

		public ColumnMapper(){
		}

		public ColumnMapper(List<String> columns){

			for(int i = 0; i < columns.size(); i++){
				String column = columns.get(i);

				putIfAbsent(column, size());
			}
		}

		public List<String> getColumns(){
			Collection<Map.Entry<String, Integer>> entries = entrySet();

			return entries.stream()
				.sorted((left, right) -> {
					return (left.getValue()).compareTo(right.getValue());
				})
				.map(entry -> entry.getKey())
				.collect(Collectors.toList());
		}
	}

	static
	private class TabularArguments extends AbstractMap<String, Object> {

		private ColumnMapper mapper = null;

		private List<?> row = null;


		public TabularArguments(ColumnMapper mapper){
			this.mapper = mapper;
		}

		@Override
		public Object get(Object key){
			Integer index = this.mapper.get(key);

			if(index != null){
				return getValue(index);
			}

			return null;
		}

		@Override
		public Set<Entry<String, Object>> entrySet(){
			throw new UnsupportedOperationException();
		}

		public Object getValue(int index){
			List<?> row = getRow();

			return row.get(index);
		}

		public List<?> getRow(){
			return this.row;
		}

		public void setRow(List<?> row){
			this.row = row;
		}
	}

	static {
		ClassLoader clazzLoader = PythonUtil.class.getClassLoader();

		PickleUtil.init(clazzLoader, "python2pmml.properties");
	}
}