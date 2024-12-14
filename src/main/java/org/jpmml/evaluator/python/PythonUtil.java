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
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
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
import org.jpmml.evaluator.Table;
import org.jpmml.evaluator.TableReader;
import org.jpmml.evaluator.TableWriter;
import org.jpmml.python.PickleUtil;

public class PythonUtil {

	private PythonUtil(){
	}

	static
	public byte[] evaluate(Evaluator evaluator, byte[] dictBytes, String[] dropColumns) throws IOException {
		Map<String, ?> arguments = (Map)unpickle(dictBytes);

		Map<String, ?> results = evaluate(evaluator, arguments, dropColumns != null ? toSet(dropColumns) : null);

		return pickle(results);
	}

	static
	public Map<String, ?> evaluate(Evaluator evaluator, Map<String, ?> arguments, Set<String> dropColumns){
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

		Map<String, ?> results = EvaluatorUtil.decodeAll(pmmlResults);

		if(dropColumns != null){
			(results.keySet()).removeAll(dropColumns);
		}

		return results;
	}

	static
	public byte[] evaluateAll(Evaluator evaluator, byte[] dictBytes, String[] dropColumns) throws IOException {
		Map<String, ?> argumentsDict = (Map)unpickle(dictBytes);

		Map<String, ?> resultsDict = evaluateAll(evaluator, argumentsDict, dropColumns != null ? toSet(dropColumns) : null);

		return pickle(resultsDict);
	}

	static
	public Map<String, ?> evaluateAll(Evaluator evaluator, Map<String, ?> argumentsDict, Set<String> dropColumns){
		Table argumentsTable = parseDict(argumentsDict);

		TableReader argumentsReader = new TableReader(argumentsTable){

			@Override
			public Object get(Object key){
				return super.get((String)key);
			}
		};

		Table resultsTable = new Table();

		TableWriter resultsWriter = new TableWriter(resultsTable){

			@Override
			public Object put(String key, Object value){

				if(dropColumns != null && dropColumns.contains(key)){
					return null;
				}

				value = EvaluatorUtil.decode(value);

				return super.put(key, value);
			}
		};

		while(argumentsReader.hasNext()){
			Map<String, ?> arguments = argumentsReader.next();

			resultsWriter.next();

			try {
				Map<String, ?> results = evaluator.evaluate(arguments);

				resultsWriter.putAll(results);
			} catch(Exception e){
				resultsWriter.put(e);
			}
		}

		resultsTable.canonicalize();

		return formatDict(resultsTable);
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
	public <E> Set<E> toSet(E[] values){

		if(values.length == 0){
			return Collections.emptySet();
		} else

		if(values.length == 1){
			return Collections.singleton(values[0]);
		} else

		{
			return new HashSet<>(Arrays.asList(values));
		}
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
	private Table parseDict(Map<String, ?> dict){
		List<String> columns = (List)dict.get("columns");
		List<List<?>> data = (List)dict.get("data");

		if(columns.size() != data.size()){
			throw new IllegalArgumentException();
		}

		Table result = new Table(columns);

		for(int i = 0; i < columns.size(); i++){
			String column = columns.get(i);
			List<?> values = data.get(i);

			result.setValues(column, values);
		}

		return result;
	}

	static
	public Map<String, ?> formatDict(Table table){
		List<String> columns = table.getColumns();
		List<List<?>> data = new ArrayList<>();

		for(int i = 0; i < columns.size(); i++){
			String column = columns.get(i);
			List<?> values = table.getValues(column);

			data.add(values);
		}

		List<Exception> exceptions = table.getExceptions();
		List<String> errors = null;

		if(containsNonNull(exceptions)){
			errors = exceptions.stream()
				.map(exception -> (exception != null ? exception.toString() : null))
				.collect(Collectors.toList());
		}

		Map<String, List<?>> result = new HashMap<>();
		result.put("columns", columns);
		result.put("data", data);
		result.put("errors", errors);

		return result;
	}

	static
	private <E> boolean containsNonNull(List<E> values){

		for(int i = 0; i < values.size(); i++){
			E value = values.get(i);

			if(value != null){
				return true;
			}
		}

		return false;
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

	static {
		ClassLoader clazzLoader = PythonUtil.class.getClassLoader();

		PickleUtil.init(clazzLoader, "python2pmml.properties");
	}
}