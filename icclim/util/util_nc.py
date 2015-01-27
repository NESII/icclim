import numpy
import util_dt

def check_att(nc, att):
    
    '''    
    Checks if a global attribut exists in a dataset.
    
    :param nc: NetCDF dataset
    :type nc: netCDF4.Dataset 
    :param att: attribut name
    :type att: str
    
    :rtype: int (1 if attribut exists, 0 else)
    
    '''
    
    try:
        nc.__getattribute__(att)
        a = 1 # attribut exists
    except AttributeError:
        a = 0 # attribut doesn't exist
    return a


def copy_att(nc1, nc2, att):
    
    '''
    Copies a global attribute from one dataset (nc1) to another (nc2).
    
    :param nc1: from
    :type nc1: netCDF4.Dataset
    :param nc2: to
    :type nc2: netCDF4.Dataset

    '''
    
    nc2.__setattr__(att, '')
    if (check_att(nc1,att)==1):
        nc2.__setattr__(att, nc1.__getattribute__(att))
        
        
def copy_var_attrs(source, destination):
    '''
    Copies all attributes from one variable (source) to another (destination).
    
    :param source: from
    :type source: netCDF4.Variable
    :param destination: to
    :type destination: netCDF4.Variable

    '''
    sourceAttrs = source.ncattrs()
    for attr in sourceAttrs:
        if attr == '_FillValue':
            pass
        else:
            destination.setncattr(attr, source.getncattr(attr))
            
            
def copy_var(variableName,sourceDataset, destinationDataset):
    '''
    Copies a variable from one dataset(sourceDataset) to another(destinationDataset) by name(variableName).
    
    :param variableName: name of variable to write
    :type variableName: str
    :param sourceDataset: from
    :type sourceDataset: netCDF4.Dataset
    :param destinationDataset: to
    :type destinationDataset: netCDF4.Dataset

    '''
    # Get the variable to copy
    sourceVar = sourceDataset.variables[variableName];
    
    # Copy the dims of the variable
    for dimname in sourceVar.dimensions:
        if destinationDataset.dimensions.has_key(dimname) == False:
            dim = rootgrp.dimensions.get(dimname)
            destinationDataset.createDimension(dimname,len(dim))
    
    # Create the variable
    destinationVariable = destinationDataset.createVariable(variableName,sourceVar.dtype, sourceVar.dimensions)
    
    #Copy its attributes
    copy_var_attrs(sourceVar,destinationVariable);
    destinationVariable[:] = sourceVar[:]
    
    
def get_att_value(nc, var, att):
    '''
    Returns an attribut value of a variable in dataset.
    
    :param nc: NetCDF dataset
    :type nc: netCDF4.Dataset
    :param var: variable name
    :type var: str
    :param att: attribut name
    :type var: str
    
    '''
    v = nc.variables[var]
    att_val = v.getncattr(att)
    return att_val


def set_time_values(nc, time_steps_arr_dt, calend, units):
    '''
    param time_steps_arr_dt: numpy array of datetime objects
    '''
    time_steps_num = numpy.array([util_dt.date2num(i, calend, units) for i in time_steps_arr_dt])
    nc.variables['time'][:] = time_steps_num[:]


def set_timebnds_values(nc, time_bnds_dt, calend, units):
    time_bnds_num = numpy.array([util_dt.date2num(i, calend, units) for i in time_bnds_dt])
    nc.variables['time_bounds'][:,:] = time_bnds_num[:,:]
    
    
def copy_var_dim(inc, onc, var): 
    '''
    Copies the spatial coordinate variables (e.g.: lat, lon) of a variable (var) from one NetCDF file (ifile) to another (out_file)
    and returns list of coordinates variables.
    
    :param inc: input dataset
    :type inc: netCDF4.Dataset
    :param onc: output dataset
    :type onc: netCDF4.Dataset
    :param var: variable name to process
    :type var: str
    :param project: project name ("CMIP5" or "CORDEX")
    :type project: str
    
    :rtype: tuple of str (coordinate variables: 'time', 'lat', 'lon')
    '''


    v = inc.variables[var]

    v_dim = v.dimensions
    
    if v.ndim == 3: # (e.g.: u'time', u'lat', u'lon')
        time_var = v_dim[0]
        lat_var = v_dim[1]
        lon_var = v_dim[2]
        
    elif v.ndim == 4: # (e.g.: u'time', u'plev', u'lat', u'lon')
        time_var = v_dim[0]
        lat_var = v_dim[-2]
        lon_var = v_dim[-1]
        
    glob_att = ['title', 'institution', 'source', 'references', 'comment', 'history']
    
    # Note: it needs to do it BEFORE the creation of var/dim
    for att in glob_att:
        copy_att(inc,onc,att)
       
    
    
        
    inc_dim0 = inc.variables[str(time_var)] # time
    inc_dim1 = inc.variables[str(lat_var)] # lat
    inc_dim2 = inc.variables[str(lon_var)] # lon

    try:
        inc_dim1_bounds = inc.variables[str(inc_dim1.__getattribute__('bounds'))]
        inc_dim2_bounds = inc.variables[str(inc_dim2.__getattribute__('bounds'))]
    except:
        pass

    
    ### create dimentions
    onc.createDimension(str(time_var), 0) # time       
    onc.createDimension(str(lat_var), v.shape[1]) # lat
    onc.createDimension(str(lon_var), v.shape[2]) # lon        
    onc.createDimension('tbnds', 2) # tbnds
    onc.createDimension('nv', 2) # nv

    
    ### create variables 
    onc_dim0 = onc.createVariable( str(time_var), inc_dim0.dtype, (str(time_var)) ) # time
    onc_dim1 = onc.createVariable( str(lat_var), inc_dim1.dtype, (str(lat_var)) ) # lat
    onc_dim2 = onc.createVariable( str(lon_var), inc_dim2.dtype, (str(lon_var)) ) # lon
    onc_time_bnds = onc.createVariable( 'time_bounds', inc_dim0.dtype, (str(time_var), 'tbnds') ) # time_bnds

    try:
        onc_dim1_bounds = onc.createVariable('lat_bounds', inc_dim1_bounds.dtype, (str(lat_var), 'nv'))
        onc_dim2_bounds = onc.createVariable('lon_bounds', inc_dim2_bounds.dtype, (str(lon_var), 'nv'))
    except:
        pass

    
    

    ### copy attributes        
    # time 
    for j in range(len(inc_dim0.ncattrs())): # set attributs of current variable       
        onc_dim0.__setattr__(  inc_dim0.__dict__.items()[j][0]  , inc_dim0.__dict__.items()[j][1])          
    # lat
    for j in range(len(inc_dim1.ncattrs())): # set attributs of current variable       
        onc_dim1.__setattr__(  inc_dim1.__dict__.items()[j][0]  , inc_dim1.__dict__.items()[j][1])  
    # lon
    for j in range(len(inc_dim2.ncattrs())): # set attributs of current variable       
        onc_dim2.__setattr__(  inc_dim2.__dict__.items()[j][0]  , inc_dim2.__dict__.items()[j][1])

    try:
        # lat_bounds
        for j in range(len(inc_dim1_bounds.ncattrs())): # set attributs of current variable       
            onc_dim1_bounds.__setattr__(  inc_dim1_bounds.__dict__.items()[j][0]  , inc_dim1_bounds.__dict__.items()[j][1])
    
        # lon_bounds
        for j in range(len(inc_dim2_bounds.ncattrs())): # set attributs of current variable       
            onc_dim2_bounds.__setattr__(  inc_dim2_bounds.__dict__.items()[j][0]  , inc_dim2_bounds.__dict__.items()[j][1])
    except:
        pass        

    
    # for time_bnds, we copy only 2 attributes of time: 'units' and 'calendar' ( => var 'time' must have these 2 attributes)
    onc_time_bnds.__setattr__( 'units', inc_dim0.__getattribute__('units') )
    try:
        onc_time_bnds.__setattr__( 'calendar', inc_dim0.__getattribute__('calendar') )
    except:
        onc_time_bnds.__setattr__( 'calendar', 'gregorian' )
    
    
    ### copy values
    onc_dim1[:] = inc_dim1[:]
    onc_dim2[:] = inc_dim2[:]
    try:
        onc_dim1_bounds[:,:] = inc_dim1_bounds[:,:]
        onc_dim2_bounds[:,:] = inc_dim2_bounds[:,:]
    except:
        pass
    #######################
    
    # Copy coordinate variables
    if check_att(v, 'coordinates')==1:
      #print "There are coordinate vars"
      coordinateAttr = v.getncattr("coordinates").split()
      for coordinate in coordinateAttr:
        #print "Copying coordidinate"+coordinate
        copy_var(coordinate,inc,onc)
    # maartenplieger comments: Is this necessary? Should copy all grid_mapping of the var to write and it will be fine.
    if check_att(v, 'grid_mapping')==1:
          c = str(v.__getattribute__('grid_mapping'))
          inc_c = inc.variables[c]
          
          onc_c = onc.createVariable( c, inc.variables[c].dtype )
          
          for j in range(len(inc_c.ncattrs())): # set attributs of current variable       
              onc_c.__setattr__(  inc_c.__dict__.items()[j][0]  , inc_c.__dict__.items()[j][1])
    
    ## maartenplieger comments: This could be removed...
    #if project == 'CORDEX_DEPRECATED':
    #
    #  if check_att(v, 'coordinates')==1:
    #      a = str(v.__getattribute__('coordinates').split()[0])
    #      b = str(v.__getattribute__('coordinates').split()[1])
    #      
    #      inc_a = inc.variables[a]
    #      inc_b = inc.variables[b]
    #      
    #      onc_a = onc.createVariable( a, inc.variables[a].dtype, ( str(lat_var), str(lon_var) ) )
    #      onc_b = onc.createVariable( b, inc.variables[b].dtype, ( str(lat_var), str(lon_var) ) )
    #  
    #      for j in range(len(inc_a.ncattrs())): # set attributs of current variable       
    #          onc_a.__setattr__(  inc_a.__dict__.items()[j][0]  , inc_a.__dict__.items()[j][1])
    #          
    #      for j in range(len(inc_b.ncattrs())): # set attributs of current variable       
    #          onc_b.__setattr__(  inc_b.__dict__.items()[j][0]  , inc_b.__dict__.items()[j][1])  
    #  
    #  if check_att(v, 'grid_mapping')==1:
    #      c = str(v.__getattribute__('grid_mapping'))
    #      inc_c = inc.variables[c]
    #      
    #      onc_c = onc.createVariable( c, inc.variables[c].dtype )
    #      
    #      for j in range(len(inc_c.ncattrs())): # set attributs of current variable       
    #          onc_c.__setattr__(  inc_c.__dict__.items()[j][0]  , inc_c.__dict__.items()[j][1])
    #          
    #          
    #  onc_a[:,:] = inc_a[:,:]
    #  onc_b[:,:] = inc_b[:,:]
    #
    #  onc_c = inc_c # ???
  
                    
            
                
    return (str(time_var), str(lat_var), str(lon_var)) # tuple ('time', 'lat', 'lon')


def get_values_arr_and_dt_arr(ncVar_temporal, ncVar_values, time_range=None, N_lev=None, spatial_chunking=False, i1_row_current_tile=None, i2_row_current_tile=None, i1_col_current_tile=None, i2_col_current_tile=None):
    
    calend = ncVar_temporal.calendar
    units=ncVar_temporal.units
    
    time_arr = ncVar_temporal[:]
    
    dt_arr = numpy.array([util_dt.num2date(dt, calend=calend, units=units) for dt in time_arr])
    
    if spatial_chunking==False:
        
        if N_lev == None:
            assert(ncVar_values.ndim == 3)
            if time_range == None:
                values_arr = ncVar_values[:,:,:]                
            else:
                indices_subset = util_dt.get_indices_subset(dt_arr, time_range)
                dt_arr = dt_arr[indices_subset].squeeze()                
                values_arr = ncVar_values[indices_subset,:,:].squeeze()
                
        else:
            assert(ncVar_values.ndim == 4)
            if time_range == None:
                values_arr = ncVar_values[:,N_lev,:,:]
            else:
                indices_subset = util_dt.get_indices_subset(dt_arr, time_range)
                dt_arr = dt_arr[indices_subset].squeeze()
                values_arr = ncVar_values[indices_subset,N_lev,:,:].squeeze()

        
    else: # spatial_chunking==True
        
        if N_lev == None:
            assert(ncVar_values.ndim == 3)
            if time_range == None:
                values_arr = ncVar_values[:,i1_row_current_tile:i2_row_current_tile, i1_col_current_tile:i2_col_current_tile]                
            else:
                indices_subset = util_dt.get_indices_subset(dt_arr, time_range)
                dt_arr = dt_arr[indices_subset].squeeze()
                values_arr = ncVar_values[indices_subset,i1_row_current_tile:i2_row_current_tile, i1_col_current_tile:i2_col_current_tile].squeeze()
                
        else:
            assert(ncVar_values.ndim == 4)
            if time_range == None:
                values_arr = ncVar_values[:,N_lev,i1_row_current_tile:i2_row_current_tile, i1_col_current_tile:i2_col_current_tile]
            else:
                indices_subset = util_dt.get_indices_subset(dt_arr, time_range)
                dt_arr = dt_arr[indices_subset].squeeze()
                values_arr = ncVar_values[indices_subset,N_lev,i1_row_current_tile:i2_row_current_tile, i1_col_current_tile:i2_col_current_tile].squeeze()
        
        

    return (dt_arr, values_arr)